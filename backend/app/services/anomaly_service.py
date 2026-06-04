from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.models.kpi_promo_performance import KpiPromoPerformance
from app.models.price import Price
from app.models.product import Product
from app.models.product_family import ProductFamily
from app.models.promotion import Promotion
from app.schemas.anomaly import BusinessAnomalyRead

# ── Anomaly type identifiers ────────────────────────────────────────────────
UNDERPERFORMING_PROMO = "UNDERPERFORMING_PROMO"
INEFFECTIVE_DISCOUNT = "INEFFECTIVE_DISCOUNT"
PRICE_ABOVE_REFERENCE = "PRICE_ABOVE_REFERENCE"
INTER_STORE_PRICE_GAP = "INTER_STORE_PRICE_GAP"

# ── UNDERPERFORMING_PROMO thresholds ────────────────────────────────────────
# revenue_uplift_rate (decimal, e.g. -0.30 = -30 %)
_UPLIFT_LOW = Decimal("-0.10")     # revenue loss < 10 %  → LOW
_UPLIFT_MEDIUM = Decimal("-0.50")  # revenue loss ≥ 50 %  → MEDIUM
_UPLIFT_HIGH = Decimal("-0.80")    # revenue loss ≥ 80 %  → HIGH

# ── INEFFECTIVE_DISCOUNT thresholds ─────────────────────────────────────────
# avg_price_discount_effect_pct (in %)
_DISCOUNT_EFFECT_ENTRY = Decimal("-20")   # effective discount ≥ 20 %
_DISCOUNT_EFFECT_HIGH = Decimal("-50")    # effective discount ≥ 50 %
_DISCOUNT_EFFECT_MEDIUM = Decimal("-30")  # effective discount ≥ 30 %

# ── PRICE_ABOVE_REFERENCE thresholds ────────────────────────────────────────
# Ratio of store price above country reference price
_REF_GAP_ENTRY = Decimal("0.05")    # > 5 %  above reference → entry
_REF_GAP_MEDIUM = Decimal("0.15")   # ≥ 15 % above reference → MEDIUM
_REF_GAP_HIGH = Decimal("0.30")     # ≥ 30 % above reference → HIGH

# ── INTER_STORE_PRICE_GAP thresholds ────────────────────────────────────────
# Absolute deviation from the national store average for the same product
_STORE_GAP_ENTRY = Decimal("0.15")   # > 15 % deviation → entry
_STORE_GAP_MEDIUM = Decimal("0.25")  # ≥ 25 % deviation → MEDIUM
_STORE_GAP_HIGH = Decimal("0.40")    # ≥ 40 % deviation → HIGH


# ── Helpers ─────────────────────────────────────────────────────────────────

def _to_decimal(value: object) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value))


def _round_decimal(value: Decimal, places: str = "0.01") -> Decimal:
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)


def _uplift_severity(uplift_rate: Decimal, family_effect_flag: str | None) -> str:
    """
    Determine UNDERPERFORMING_PROMO severity.

    Cannibalization escalates severity by one level:
    MEDIUM + CANNIBALIZATION → HIGH.
    """
    if uplift_rate <= _UPLIFT_HIGH:
        return "HIGH"

    if uplift_rate <= _UPLIFT_MEDIUM or family_effect_flag == "CANNIBALIZATION":
        return (
            "HIGH"
            if family_effect_flag == "CANNIBALIZATION" and uplift_rate <= _UPLIFT_MEDIUM
            else "MEDIUM"
        )

    return "LOW"


def _discount_severity(discount_effect_pct: Decimal) -> str:
    if discount_effect_pct <= _DISCOUNT_EFFECT_HIGH:
        return "HIGH"
    if discount_effect_pct <= _DISCOUNT_EFFECT_MEDIUM:
        return "MEDIUM"
    return "LOW"


def _ref_gap_severity(gap_rate: Decimal) -> str:
    if gap_rate >= _REF_GAP_HIGH:
        return "HIGH"
    if gap_rate >= _REF_GAP_MEDIUM:
        return "MEDIUM"
    return "LOW"


def _store_gap_severity(gap_rate: Decimal) -> str:
    if gap_rate >= _STORE_GAP_HIGH:
        return "HIGH"
    if gap_rate >= _STORE_GAP_MEDIUM:
        return "MEDIUM"
    return "LOW"


def _family_name_by_id(db: Session, family_id: int) -> str | None:
    row = db.execute(
        select(ProductFamily.name).where(ProductFamily.id == family_id)
    ).scalar_one_or_none()
    return row


def _active_promotion_ids(db: Session) -> set[int]:
    rows = db.execute(
        select(Promotion.id).where(Promotion.active)
    ).scalars().all()
    return set(rows)


def _quota_per_severity(limit: int) -> dict[str, int]:
    """
    Split total quota across the 3 severity levels.
    HIGH gets half; MEDIUM and LOW share the remainder.
    Guarantees at least 1 result per level when possible.
    """
    high = max(limit // 2, 1)
    medium = max((limit - high) // 2, 1)
    low = max(limit - high - medium, 1)
    return {"HIGH": high, "MEDIUM": medium, "LOW": low}


# ── Rule 1: UNDERPERFORMING_PROMO ────────────────────────────────────────────

def _get_underperforming_promos(
    db: Session,
    promotion_id: int | None,
    product_id: int | None,
    store_id: int | None,
    allowed_store_ids: list[int] | None,
    limit: int,
) -> list[BusinessAnomalyRead]:
    """
    Detect promotions whose daily revenue is below pre-promotion baseline.

    Source : pct_analytics.kpi_promo_performance (dbt mart)
    Baseline : 14-day window before promotion start, normalised to daily average.

    Entry criterion : revenue_uplift_rate < -10 %

    Severity:
    - LOW    : uplift between -10 % and -50 %
    - MEDIUM : uplift ≤ -50 %, or negative uplift with CANNIBALIZATION
    - HIGH   : uplift ≤ -80 %, or uplift ≤ -50 % with CANNIBALIZATION

    Promotions flagged NOT_COMPARABLE (new product, no baseline) are excluded
    and handled by the INEFFECTIVE_DISCOUNT rule instead.
    """
    active_ids = _active_promotion_ids(db)

    def _base_query():
        q = (
            select(KpiPromoPerformance)
            .where(KpiPromoPerformance.promo_performance_flag != "NOT_COMPARABLE")
            .where(KpiPromoPerformance.revenue_uplift_rate.is_not(None))
        )
        if active_ids:
            q = q.where(KpiPromoPerformance.promotion_id.in_(active_ids))
        if promotion_id is not None:
            q = q.where(KpiPromoPerformance.promotion_id == promotion_id)
        if product_id is not None:
            q = q.where(KpiPromoPerformance.product_id == product_id)
        if store_id is not None:
            q = q.where(KpiPromoPerformance.store_id == store_id)
        elif allowed_store_ids is not None:
            q = q.where(KpiPromoPerformance.store_id.in_(allowed_store_ids))
        return q

    quotas = _quota_per_severity(limit)

    rows_high = db.execute(
        _base_query()
        .where(KpiPromoPerformance.revenue_uplift_rate <= float(_UPLIFT_HIGH))
        .order_by(KpiPromoPerformance.revenue_uplift_rate.asc())
        .limit(quotas["HIGH"])
    ).scalars().all()

    rows_medium = db.execute(
        _base_query()
        .where(KpiPromoPerformance.revenue_uplift_rate > float(_UPLIFT_HIGH))
        .where(KpiPromoPerformance.revenue_uplift_rate <= float(_UPLIFT_MEDIUM))
        .order_by(KpiPromoPerformance.revenue_uplift_rate.asc())
        .limit(quotas["MEDIUM"])
    ).scalars().all()

    rows_low = db.execute(
        _base_query()
        .where(KpiPromoPerformance.revenue_uplift_rate > float(_UPLIFT_MEDIUM))
        .where(KpiPromoPerformance.revenue_uplift_rate < float(_UPLIFT_LOW))
        .order_by(KpiPromoPerformance.revenue_uplift_rate.asc())
        .limit(quotas["LOW"])
    ).scalars().all()

    rows = list(rows_high) + list(rows_medium) + list(rows_low)

    family_cache: dict[int, str | None] = {}
    anomalies: list[BusinessAnomalyRead] = []

    for row in rows:
        uplift_rate = _to_decimal(row.revenue_uplift_rate)
        uplift_pct = _round_decimal(uplift_rate * 100, "0.1")
        promo_revenue = _round_decimal(_to_decimal(row.promo_revenue))
        baseline_daily = _round_decimal(_to_decimal(row.baseline_daily_revenue))
        expected_revenue = _round_decimal(
            _to_decimal(row.baseline_daily_revenue) * _to_decimal(row.promo_period_days)
        )

        severity = _uplift_severity(uplift_rate, row.family_effect_flag)

        if row.product_family_id not in family_cache:
            family_cache[row.product_family_id] = _family_name_by_id(db, row.product_family_id)
        family_name = family_cache[row.product_family_id]

        cannibal_note = (
            " De plus, les autres produits de la famille ont subi une baisse de CA "
            "(effet de cannibalisation)."
            if row.family_effect_flag == "CANNIBALIZATION"
            else ""
        )

        anomalies.append(
            BusinessAnomalyRead(
                anomaly_type=UNDERPERFORMING_PROMO,
                severity=severity,
                message=(
                    f"La promotion {row.promotion_id} a généré {uplift_pct} % de CA par jour "
                    f"par rapport à la période sans promo (baseline : {baseline_daily} €/j). "
                    f"CA total promo : {promo_revenue} € vs {expected_revenue} € attendu."
                    f"{cannibal_note}"
                ),
                promotion_id=row.promotion_id,
                promotion_active=row.promotion_id in active_ids,
                product_id=row.product_id,
                product_family_name=family_name,
                store_id=row.store_id,
                sales_count=int(_to_decimal(row.promo_quantity)),
                total_quantity=int(_to_decimal(row.promo_quantity)),
                total_revenue=promo_revenue,
                threshold=expected_revenue,
            )
        )

    return anomalies


# ── Rule 2: INEFFECTIVE_DISCOUNT ─────────────────────────────────────────────

def _get_ineffective_discount_promos(
    db: Session,
    promotion_id: int | None,
    product_id: int | None,
    store_id: int | None,
    allowed_store_ids: list[int] | None,
    limit: int,
) -> list[BusinessAnomalyRead]:
    """
    Detect promotions with a significant effective discount but no volume uplift
    (margin is sacrificed without attracting more customers).

    Criteria:
    - avg_price_discount_effect_pct ≤ -20 % (price dropped by at least 20 %)
    - quantity_uplift_rate ≤ 0 (volume did not increase)

    Also covers new products (NOT_COMPARABLE) when the discount exceeds 50 % of
    the reference price — likely a data-entry error.

    Severity:
    - LOW    : effective discount between -20 % and -30 %
    - MEDIUM : effective discount between -30 % and -50 %
    - HIGH   : effective discount ≥ 50 %
    """
    active_ids = _active_promotion_ids(db)

    def _disc_base_query():
        q = (
            select(KpiPromoPerformance)
            .where(KpiPromoPerformance.avg_price_discount_effect_pct.is_not(None))
            .where(
                KpiPromoPerformance.avg_price_discount_effect_pct
                <= float(_DISCOUNT_EFFECT_ENTRY)
            )
            .where(
                (KpiPromoPerformance.quantity_uplift_rate <= 0)
                | (KpiPromoPerformance.promo_performance_flag == "NOT_COMPARABLE")
            )
        )
        if active_ids:
            q = q.where(KpiPromoPerformance.promotion_id.in_(active_ids))
        if promotion_id is not None:
            q = q.where(KpiPromoPerformance.promotion_id == promotion_id)
        if product_id is not None:
            q = q.where(KpiPromoPerformance.product_id == product_id)
        if store_id is not None:
            q = q.where(KpiPromoPerformance.store_id == store_id)
        elif allowed_store_ids is not None:
            q = q.where(KpiPromoPerformance.store_id.in_(allowed_store_ids))
        return q

    quotas = _quota_per_severity(limit)

    disc_high = db.execute(
        _disc_base_query()
        .where(KpiPromoPerformance.avg_price_discount_effect_pct <= float(_DISCOUNT_EFFECT_HIGH))
        .order_by(KpiPromoPerformance.avg_price_discount_effect_pct.asc())
        .limit(quotas["HIGH"])
    ).scalars().all()

    disc_medium = db.execute(
        _disc_base_query()
        .where(KpiPromoPerformance.avg_price_discount_effect_pct > float(_DISCOUNT_EFFECT_HIGH))
        .where(KpiPromoPerformance.avg_price_discount_effect_pct <= float(_DISCOUNT_EFFECT_MEDIUM))
        .order_by(KpiPromoPerformance.avg_price_discount_effect_pct.asc())
        .limit(quotas["MEDIUM"])
    ).scalars().all()

    disc_low = db.execute(
        _disc_base_query()
        .where(KpiPromoPerformance.avg_price_discount_effect_pct > float(_DISCOUNT_EFFECT_MEDIUM))
        .order_by(KpiPromoPerformance.avg_price_discount_effect_pct.asc())
        .limit(quotas["LOW"])
    ).scalars().all()

    rows = list(disc_high) + list(disc_medium) + list(disc_low)

    family_cache: dict[int, str | None] = {}
    anomalies: list[BusinessAnomalyRead] = []

    for row in rows:
        discount_pct = _to_decimal(row.avg_price_discount_effect_pct)
        severity = _discount_severity(discount_pct)

        promo_revenue = _round_decimal(_to_decimal(row.promo_revenue))
        promo_price = _round_decimal(_to_decimal(row.promo_avg_selling_price))
        baseline_price = _round_decimal(_to_decimal(row.baseline_avg_selling_price))

        if row.product_family_id not in family_cache:
            family_cache[row.product_family_id] = _family_name_by_id(db, row.product_family_id)
        family_name = family_cache[row.product_family_id]

        is_new_product = row.promo_performance_flag == "NOT_COMPARABLE"
        context = (
            "Nouveau produit sans historique de vente — remise potentiellement erronée."
            if is_new_product
            else (
                f"Le volume vendu n'a pas augmenté malgré la remise (uplift quantité : "
                f"{_round_decimal(_to_decimal(row.quantity_uplift_rate) * 100, '0.1')} %)."
            )
        )

        anomalies.append(
            BusinessAnomalyRead(
                anomaly_type=INEFFECTIVE_DISCOUNT,
                severity=severity,
                message=(
                    f"La promotion {row.promotion_id} affiche une remise effective de "
                    f"{_round_decimal(abs(discount_pct), '0.1')} % sur le prix de vente "
                    f"(avant : {baseline_price} €, pendant : {promo_price} €). {context}"
                ),
                promotion_id=row.promotion_id,
                promotion_active=row.promotion_id in active_ids,
                product_id=row.product_id,
                product_family_name=family_name,
                store_id=row.store_id,
                sales_count=int(_to_decimal(row.promo_quantity)),
                total_quantity=int(_to_decimal(row.promo_quantity)),
                total_revenue=promo_revenue,
                threshold=_round_decimal(_to_decimal(row.baseline_avg_selling_price)),
            )
        )

    return anomalies


# ── Rule 3: PRICE_ABOVE_REFERENCE ────────────────────────────────────────────

def _get_price_above_reference(
    db: Session,
    product_id: int | None,
    store_id: int | None,
    allowed_store_ids: list[int] | None,
    limit: int,
) -> list[BusinessAnomalyRead]:
    """
    Detect active store-level prices exceeding the national reference price.

    Source : pct_core.price
    Comparison : store price (price_scope=STORE, price_type=STANDARD, status=ACTIVE)
                 vs country reference (price_scope=COUNTRY, price_type=STANDARD, status=ACTIVE)
                 for the same product and country.

    Entry criterion : store_price > reference_price × 1.05

    Severity:
    - LOW    : 5 % – 15 % above reference
    - MEDIUM : 15 % – 30 % above reference
    - HIGH   : ≥ 30 % above reference
    """
    today = date.today()

    StorePrice = aliased(Price, name="store_price")
    RefPrice = aliased(Price, name="ref_price")

    def _base_query():
        gap = (StorePrice.amount - RefPrice.amount) / RefPrice.amount
        q = (
            select(
                StorePrice.product_id,
                StorePrice.store_id,
                StorePrice.amount.label("store_amount"),
                RefPrice.amount.label("ref_amount"),
                Product.product_family_id,
                gap.label("gap_rate"),
            )
            .join(
                RefPrice,
                and_(
                    RefPrice.product_id == StorePrice.product_id,
                    RefPrice.country_id == StorePrice.country_id,
                    RefPrice.price_scope == "COUNTRY",
                    RefPrice.price_type == "STANDARD",
                    RefPrice.status == "ACTIVE",
                    or_(RefPrice.effective_to.is_(None), RefPrice.effective_to >= today),
                ),
            )
            .join(Product, Product.id == StorePrice.product_id)
            .where(StorePrice.price_scope == "STORE")
            .where(StorePrice.price_type == "STANDARD")
            .where(StorePrice.status == "ACTIVE")
            .where(or_(StorePrice.effective_to.is_(None), StorePrice.effective_to >= today))
            .where(gap > float(_REF_GAP_ENTRY))
        )
        if product_id is not None:
            q = q.where(StorePrice.product_id == product_id)
        if store_id is not None:
            q = q.where(StorePrice.store_id == store_id)
        elif allowed_store_ids is not None:
            q = q.where(StorePrice.store_id.in_(allowed_store_ids))
        return q

    quotas = _quota_per_severity(limit)

    rows_high = db.execute(
        _base_query()
        .where(
            (StorePrice.amount - RefPrice.amount) / RefPrice.amount >= float(_REF_GAP_HIGH)
        )
        .order_by(((StorePrice.amount - RefPrice.amount) / RefPrice.amount).desc())
        .limit(quotas["HIGH"])
    ).all()

    rows_medium = db.execute(
        _base_query()
        .where(
            (StorePrice.amount - RefPrice.amount) / RefPrice.amount >= float(_REF_GAP_MEDIUM)
        )
        .where(
            (StorePrice.amount - RefPrice.amount) / RefPrice.amount < float(_REF_GAP_HIGH)
        )
        .order_by(((StorePrice.amount - RefPrice.amount) / RefPrice.amount).desc())
        .limit(quotas["MEDIUM"])
    ).all()

    rows_low = db.execute(
        _base_query()
        .where(
            (StorePrice.amount - RefPrice.amount) / RefPrice.amount < float(_REF_GAP_MEDIUM)
        )
        .order_by(((StorePrice.amount - RefPrice.amount) / RefPrice.amount).desc())
        .limit(quotas["LOW"])
    ).all()

    rows = list(rows_high) + list(rows_medium) + list(rows_low)

    family_cache: dict[int, str | None] = {}
    anomalies: list[BusinessAnomalyRead] = []

    for row in rows:
        store_amount = _round_decimal(_to_decimal(row.store_amount))
        ref_amount = _round_decimal(_to_decimal(row.ref_amount))
        gap_rate = _to_decimal(row.gap_rate)
        gap_pct = _round_decimal(gap_rate * 100, "0.1")
        severity = _ref_gap_severity(gap_rate)

        if row.product_family_id not in family_cache:
            family_cache[row.product_family_id] = _family_name_by_id(db, row.product_family_id)
        family_name = family_cache[row.product_family_id]

        anomalies.append(
            BusinessAnomalyRead(
                anomaly_type=PRICE_ABOVE_REFERENCE,
                severity=severity,
                message=(
                    f"Le prix du produit {row.product_id} en magasin {row.store_id} "
                    f"({store_amount} €) dépasse le prix de référence national "
                    f"({ref_amount} €) de {gap_pct} %."
                ),
                product_id=row.product_id,
                product_family_name=family_name,
                store_id=row.store_id,
                total_revenue=store_amount,
                threshold=ref_amount,
            )
        )

    return anomalies


# ── Rule 4: INTER_STORE_PRICE_GAP ────────────────────────────────────────────

def _get_inter_store_price_gaps(
    db: Session,
    product_id: int | None,
    store_id: int | None,
    allowed_store_ids: list[int] | None,
    limit: int,
) -> list[BusinessAnomalyRead]:
    """
    Detect stores whose active standard price deviates abnormally from
    the national store average for the same product.

    Source : pct_core.price
    Requires at least 2 stores with an active STORE-scope STANDARD price
    for the same product to compute a meaningful average.

    Entry criterion : |store_price − national_avg| / national_avg > 15 %

    Severity:
    - LOW    : 15 % – 25 % deviation
    - MEDIUM : 25 % – 40 % deviation
    - HIGH   : ≥ 40 % deviation
    """
    today = date.today()

    # Subquery: compute per-product national average across all stores
    stats_subq = (
        select(
            Price.product_id,
            Price.country_id,
            func.avg(Price.amount).label("avg_price"),
            func.count().label("store_count"),
        )
        .where(Price.price_scope == "STORE")
        .where(Price.price_type == "STANDARD")
        .where(Price.status == "ACTIVE")
        .where(or_(Price.effective_to.is_(None), Price.effective_to >= today))
        .group_by(Price.product_id, Price.country_id)
        .having(func.count() >= 2)
        .subquery()
    )

    gap_expr = (
        func.abs(Price.amount - stats_subq.c.avg_price) / stats_subq.c.avg_price
    )

    def _base_query():
        q = (
            select(
                Price.product_id,
                Price.store_id,
                Price.amount,
                stats_subq.c.avg_price,
                stats_subq.c.store_count,
                Product.product_family_id,
                gap_expr.label("gap_rate"),
            )
            .join(
                stats_subq,
                and_(
                    Price.product_id == stats_subq.c.product_id,
                    Price.country_id == stats_subq.c.country_id,
                ),
            )
            .join(Product, Product.id == Price.product_id)
            .where(Price.price_scope == "STORE")
            .where(Price.price_type == "STANDARD")
            .where(Price.status == "ACTIVE")
            .where(or_(Price.effective_to.is_(None), Price.effective_to >= today))
            .where(gap_expr > float(_STORE_GAP_ENTRY))
        )
        if product_id is not None:
            q = q.where(Price.product_id == product_id)
        if store_id is not None:
            q = q.where(Price.store_id == store_id)
        elif allowed_store_ids is not None:
            q = q.where(Price.store_id.in_(allowed_store_ids))
        return q

    quotas = _quota_per_severity(limit)

    rows_high = db.execute(
        _base_query()
        .where(gap_expr >= float(_STORE_GAP_HIGH))
        .order_by(gap_expr.desc())
        .limit(quotas["HIGH"])
    ).all()

    rows_medium = db.execute(
        _base_query()
        .where(gap_expr >= float(_STORE_GAP_MEDIUM))
        .where(gap_expr < float(_STORE_GAP_HIGH))
        .order_by(gap_expr.desc())
        .limit(quotas["MEDIUM"])
    ).all()

    rows_low = db.execute(
        _base_query()
        .where(gap_expr > float(_STORE_GAP_ENTRY))
        .where(gap_expr < float(_STORE_GAP_MEDIUM))
        .order_by(gap_expr.desc())
        .limit(quotas["LOW"])
    ).all()

    rows = list(rows_high) + list(rows_medium) + list(rows_low)

    family_cache: dict[int, str | None] = {}
    anomalies: list[BusinessAnomalyRead] = []

    for row in rows:
        store_price = _round_decimal(_to_decimal(row.amount))
        avg_price = _round_decimal(_to_decimal(row.avg_price))
        gap_rate = abs(_to_decimal(row.amount) - _to_decimal(row.avg_price)) / _to_decimal(
            row.avg_price
        )
        gap_pct = _round_decimal(gap_rate * 100, "0.1")
        severity = _store_gap_severity(gap_rate)

        if row.product_family_id not in family_cache:
            family_cache[row.product_family_id] = _family_name_by_id(db, row.product_family_id)
        family_name = family_cache[row.product_family_id]

        direction = "au-dessus" if _to_decimal(row.amount) > _to_decimal(row.avg_price) else "en dessous"

        anomalies.append(
            BusinessAnomalyRead(
                anomaly_type=INTER_STORE_PRICE_GAP,
                severity=severity,
                message=(
                    f"Le prix du produit {row.product_id} en magasin {row.store_id} "
                    f"({store_price} €) s'écarte de {gap_pct} % {direction} "
                    f"du prix moyen inter-magasins ({avg_price} €, "
                    f"calculé sur {row.store_count} magasins)."
                ),
                product_id=row.product_id,
                product_family_name=family_name,
                store_id=row.store_id,
                total_revenue=store_price,
                threshold=avg_price,
            )
        )

    return anomalies


# ── Public entry point ────────────────────────────────────────────────────────

def get_business_anomalies(
    db: Session,
    promotion_id: int | None = None,
    product_id: int | None = None,
    store_id: int | None = None,
    allowed_store_ids: list[int] | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[BusinessAnomalyRead], int]:
    """
    Detect pricing and commercial anomalies.

    Four rules are applied:

    1. UNDERPERFORMING_PROMO
       Daily promotion revenue below pre-promotion baseline (uplift < -10 %).
       → Promotions that destroy value without attracting customers.
       Severity: LOW (-10 % to -50 %), MEDIUM (≤ -50 % or + cannibalization),
                 HIGH (≤ -80 % or ≤ -50 % + cannibalization)

    2. INEFFECTIVE_DISCOUNT
       Effective discount ≥ 20 % with no volume uplift.
       → Margin sacrificed with no commercial benefit.
       Also covers entry-error risk on new products (no baseline, discount ≥ 50 %).
       Severity: LOW (20–30 %), MEDIUM (30–50 %), HIGH (≥ 50 %)

    3. PRICE_ABOVE_REFERENCE
       Active store-level standard price exceeds the national reference price.
       → Store sells above catalog price, damaging brand consistency.
       Severity: LOW (5–15 %), MEDIUM (15–30 %), HIGH (≥ 30 %)

    4. INTER_STORE_PRICE_GAP
       Store price deviates abnormally from the national store average.
       → Pricing inconsistency between stores for the same product.
       Requires ≥ 2 stores with active prices to compute a meaningful average.
       Severity: LOW (15–25 %), MEDIUM (25–40 %), HIGH (≥ 40 %)

    Returns a (items, total) tuple where total is the count before pagination.
    """
    fetch_limit = offset + limit

    underperforming = _get_underperforming_promos(
        db=db,
        promotion_id=promotion_id,
        product_id=product_id,
        store_id=store_id,
        allowed_store_ids=allowed_store_ids,
        limit=fetch_limit,
    )
    ineffective = _get_ineffective_discount_promos(
        db=db,
        promotion_id=promotion_id,
        product_id=product_id,
        store_id=store_id,
        allowed_store_ids=allowed_store_ids,
        limit=fetch_limit,
    )
    above_reference = _get_price_above_reference(
        db=db,
        product_id=product_id,
        store_id=store_id,
        allowed_store_ids=allowed_store_ids,
        limit=fetch_limit,
    )
    inter_store_gaps = _get_inter_store_price_gaps(
        db=db,
        product_id=product_id,
        store_id=store_id,
        allowed_store_ids=allowed_store_ids,
        limit=fetch_limit,
    )

    all_anomalies = underperforming + ineffective + above_reference + inter_store_gaps
    total = len(all_anomalies)
    page_items = all_anomalies[offset : offset + limit]
    return page_items, total
