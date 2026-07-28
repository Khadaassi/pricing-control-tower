"""Concurrency coverage for approve_and_apply_price_change_request.

Two concurrent approvals on the same PENDING request must not both succeed. The fix is a
`with_for_update()` row lock in price_change_request_service.py — this file proves that lock
actually blocks a concurrent reader (deterministic, timing-based) and then checks the resulting
end-to-end business outcome (only one of two concurrent approvals wins).
"""

import threading
import time

from sqlalchemy import select

from app.db import SessionLocal
from app.models.price import Price
from app.models.price_history import PriceHistory
from app.schemas.price_change_request import PriceChangeRequestCreate
from app.services.price_change_request_service import (
    approve_and_apply_price_change_request,
    create_price_change_request,
    lock_price_change_request_for_update,
)


def _seed_pending_request(workflow_test_data, amount: str, effective_date: str) -> int:
    with SessionLocal() as db:
        request = create_price_change_request(
            db=db,
            payload=PriceChangeRequestCreate(
                product_id=workflow_test_data["product_id"],
                country_id=workflow_test_data["country_id"],
                store_id=None,
                requested_price_amount=amount,
                justification="Concurrency test seed request",
                requested_effective_date=effective_date,
            ),
            requested_by_user_id=workflow_test_data["user_id"],
        )
        return request.id


def test_with_for_update_blocks_a_concurrent_reader(workflow_test_data):
    """Deterministic proof that the row lock is real: calls the *actual* production helper
    (lock_price_change_request_for_update) twice concurrently and asserts the second call stays
    blocked while the first holder has not committed/rolled back yet. Unlike a test that builds
    its own `.with_for_update()` query, this fails if the fix is ever removed from the service."""
    request_id = _seed_pending_request(workflow_test_data, "19.00", "2026-07-01")

    holder_has_lock = threading.Event()
    release_lock = threading.Event()
    second_reader_done = threading.Event()
    timings: dict[str, float] = {}

    def hold_lock():
        db = SessionLocal()
        try:
            lock_price_change_request_for_update(db, request_id)
            holder_has_lock.set()
            release_lock.wait(timeout=5)
        finally:
            db.commit()
            db.close()

    def try_read():
        holder_has_lock.wait(timeout=5)
        db = SessionLocal()
        try:
            start = time.monotonic()
            lock_price_change_request_for_update(db, request_id)
            timings["blocked_seconds"] = time.monotonic() - start
        finally:
            db.commit()
            db.close()
            second_reader_done.set()

    holder_thread = threading.Thread(target=hold_lock)
    reader_thread = threading.Thread(target=try_read)
    holder_thread.start()
    reader_thread.start()

    assert holder_has_lock.wait(timeout=5), "lock holder never acquired the row lock"

    # The second reader must still be blocked here — it hasn't been released yet.
    still_blocked = not second_reader_done.wait(timeout=0.3)
    assert still_blocked, "a second SELECT ... FOR UPDATE was not blocked by the row lock"

    release_lock.set()
    holder_thread.join(timeout=5)
    reader_thread.join(timeout=5)

    assert second_reader_done.is_set()
    assert timings["blocked_seconds"] >= 0.25, (
        f"second reader unblocked too early ({timings.get('blocked_seconds')}s) — "
        "lock does not appear to have been held"
    )


def test_concurrent_approvals_only_one_succeeds(workflow_test_data):
    request_id = _seed_pending_request(workflow_test_data, "49.99", "2026-07-01")

    results: list[tuple[bool, str | None]] = []
    barrier = threading.Barrier(2)

    def approve_attempt():
        db = SessionLocal()
        try:
            barrier.wait(timeout=5)
            approve_and_apply_price_change_request(
                db=db,
                price_change_request_id=request_id,
                performed_by_user_id=workflow_test_data["user_id"],
            )
            results.append((True, None))
        except Exception as exc:  # noqa: BLE001 - capturing for assertion, not re-raising
            results.append((False, str(exc)))
        finally:
            db.close()

    threads = [threading.Thread(target=approve_attempt) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    successes = [r for r in results if r[0]]
    failures = [r for r in results if not r[0]]

    assert len(successes) == 1, f"expected exactly 1 success, got {results}"
    assert len(failures) == 1

    with SessionLocal() as verify_db:
        new_prices = verify_db.scalars(
            select(Price).where(
                Price.product_id == workflow_test_data["product_id"],
                Price.amount == 49.99,
            )
        ).all()
        assert len(new_prices) == 1, "two concurrent approvals created more than one Price row"

        price_histories = verify_db.scalars(
            select(PriceHistory).where(
                PriceHistory.price_change_request_id == request_id
            )
        ).all()
        assert len(price_histories) == 1
