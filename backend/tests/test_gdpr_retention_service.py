from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.models.audit_log import AuditLog
from app.models.price import Price
from app.models.price_change_request import PriceChangeRequest
from app.models.price_history import PriceHistory
from app.models.user_account import UserAccount
from app.services.gdpr_retention_service import (
    anonymize_inactive_users,
    purge_old_history,
    run_gdpr_retention_cleanup,
)

FIXED_NOW = datetime(2026, 8, 27, tzinfo=UTC)


def _make_user(db_session, *, last_active_at, active=True) -> UserAccount:
    suffix = uuid4().hex[:8].lower()
    user = UserAccount(
        email=f"gdpr.test.{suffix}@pricing-control-tower.local",
        full_name=f"GDPR Test User {suffix}",
        active=active,
        last_active_at=last_active_at,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestAnonymizeInactiveUsers:
    def test_anonymizes_users_inactive_for_over_a_year(self, db_session):
        stale_user = _make_user(
            db_session, last_active_at=FIXED_NOW - timedelta(days=400)
        )

        count = anonymize_inactive_users(db_session, now=FIXED_NOW)

        db_session.refresh(stale_user)
        assert count == 1
        assert stale_user.active is False
        expected_email = f"anonymized-user-{stale_user.id}@deleted.pricing-control-tower.local"
        assert stale_user.email == expected_email
        assert stale_user.full_name == "Utilisateur anonymisé"

    def test_does_not_touch_recently_active_users(self, db_session):
        recent_user = _make_user(
            db_session, last_active_at=FIXED_NOW - timedelta(days=10)
        )
        original_email = recent_user.email

        count = anonymize_inactive_users(db_session, now=FIXED_NOW)

        db_session.refresh(recent_user)
        assert count == 0
        assert recent_user.active is True
        assert recent_user.email == original_email

    def test_does_not_touch_users_with_no_recorded_activity(self, db_session):
        never_active_user = _make_user(db_session, last_active_at=None)
        original_email = never_active_user.email

        count = anonymize_inactive_users(db_session, now=FIXED_NOW)

        db_session.refresh(never_active_user)
        assert count == 0
        assert never_active_user.active is True
        assert never_active_user.email == original_email

    def test_is_idempotent_on_a_second_run(self, db_session):
        _make_user(db_session, last_active_at=FIXED_NOW - timedelta(days=400))

        first_run = anonymize_inactive_users(db_session, now=FIXED_NOW)
        second_run = anonymize_inactive_users(db_session, now=FIXED_NOW)

        assert first_run == 1
        assert second_run == 0


class TestPurgeOldHistory:
    def _make_price_change_request(self, db_session, workflow_test_data) -> PriceChangeRequest:
        pcr = PriceChangeRequest(
            product_id=workflow_test_data["product_id"],
            country_id=workflow_test_data["country_id"],
            store_id=None,
            current_price_id=workflow_test_data["current_price_id"],
            old_price_amount=Decimal("19.99"),
            requested_price_amount=Decimal("24.99"),
            status="APPLIED",
            justification="Test fixture for GDPR purge",
            requested_effective_date=date(2026, 1, 1),
            requested_by_user_id=workflow_test_data["user_id"],
        )
        db_session.add(pcr)
        db_session.commit()
        db_session.refresh(pcr)
        return pcr

    def _make_new_price(self, db_session, workflow_test_data) -> Price:
        # ck_price_history_previous_new_price_different requires a second,
        # distinct price row distinct from workflow_test_data's current_price_id.
        new_price = Price(
            product_id=workflow_test_data["product_id"],
            country_id=workflow_test_data["country_id"],
            store_id=None,
            price_scope="COUNTRY",
            price_type="STANDARD",
            amount=Decimal("24.99"),
            currency_code="EUR",
            effective_from=date(2026, 2, 1),
            effective_to=None,
            status="ACTIVE",
            promotion_id=None,
            reason="Second price fixture for GDPR purge test",
            created_by=workflow_test_data["user_id"],
        )
        db_session.add(new_price)
        db_session.commit()
        db_session.refresh(new_price)
        return new_price

    def test_purges_only_rows_past_the_retention_window(
        self, db_session, workflow_test_data
    ):
        old_pcr = self._make_price_change_request(db_session, workflow_test_data)
        recent_pcr = self._make_price_change_request(db_session, workflow_test_data)
        new_price = self._make_new_price(db_session, workflow_test_data)

        old_created_at = FIXED_NOW - timedelta(days=4 * 365)
        recent_created_at = FIXED_NOW - timedelta(days=10)

        db_session.add(
            AuditLog(
                price_change_request_id=old_pcr.id,
                action_type="REQUEST_APPROVED",
                performed_by_user_id=workflow_test_data["user_id"],
                description="Old audit row, past the 3-year retention window",
                created_at=old_created_at,
            )
        )
        db_session.add(
            AuditLog(
                price_change_request_id=recent_pcr.id,
                action_type="REQUEST_APPROVED",
                performed_by_user_id=workflow_test_data["user_id"],
                description="Recent audit row, within the retention window",
                created_at=recent_created_at,
            )
        )
        db_session.add(
            PriceHistory(
                price_change_request_id=old_pcr.id,
                previous_price_id=workflow_test_data["current_price_id"],
                new_price_id=new_price.id,
                old_price_amount=Decimal("19.99"),
                new_price_amount=Decimal("24.99"),
                applied_by_user_id=workflow_test_data["user_id"],
                created_at=old_created_at,
            )
        )
        db_session.add(
            PriceHistory(
                price_change_request_id=recent_pcr.id,
                previous_price_id=workflow_test_data["current_price_id"],
                new_price_id=new_price.id,
                old_price_amount=Decimal("19.99"),
                new_price_amount=Decimal("24.99"),
                applied_by_user_id=workflow_test_data["user_id"],
                created_at=recent_created_at,
            )
        )
        db_session.commit()

        purged_audit_log_rows, purged_price_history_rows = purge_old_history(
            db_session, now=FIXED_NOW
        )

        assert purged_audit_log_rows == 1
        assert purged_price_history_rows == 1

        remaining_audit_log = (
            db_session.query(AuditLog)
            .filter(AuditLog.price_change_request_id.in_([old_pcr.id, recent_pcr.id]))
            .all()
        )
        remaining_price_history = (
            db_session.query(PriceHistory)
            .filter(
                PriceHistory.price_change_request_id.in_([old_pcr.id, recent_pcr.id])
            )
            .all()
        )

        assert [row.price_change_request_id for row in remaining_audit_log] == [
            recent_pcr.id
        ]
        assert [row.price_change_request_id for row in remaining_price_history] == [
            recent_pcr.id
        ]


class TestRunGdprRetentionCleanup:
    def test_returns_a_summary_of_both_operations(self, db_session):
        _make_user(db_session, last_active_at=FIXED_NOW - timedelta(days=400))

        result = run_gdpr_retention_cleanup(db_session, now=FIXED_NOW)

        assert result.anonymized_users == 1
        assert result.purged_audit_log_rows == 0
        assert result.purged_price_history_rows == 0
