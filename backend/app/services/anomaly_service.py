from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.kpi_promo_performance import KpiPromoPerformance
from app.models.product_family import ProductFamily
from app.schemas.anomaly import BusinessAnomalyRead

UNDERPERFORMING_PROMO = "UNDERPERFORMING_PROMO"
INEFFECTIVE_DISCOUNT = "INEFFECTIVE_DISCOUNT"

# Seuils d'uplift de CA (décimal, ex : -0.30 = -30 %)
# Comparaison : CA quotidien pendant la promo vs CA quotidien 14j avant
_UPLIFT_LOW = Decimal("-0.10")    # perte de CA < 10 %  → LOW
_UPLIFT_MEDIUM = Decimal("-0.50") # perte de CA ≥ 50 %  → MEDIUM
_UPLIFT_HIGH = Decimal("-0.80")   # perte de CA ≥ 80 %  → HIGH

# Seuil de remise effective (avg_price_discount_effect_pct, en %)
# Remise effective = (prix_vente_promo - prix_vente_avant) / prix_vente_avant × 100
# Négatif = le prix a baissé pendant la promo
_DISCOUNT_EFFECT_ENTRY = Decimal("-20")   # remise effective ≥ 20 %
_DISCOUNT_EFFECT_HIGH = Decimal("-50")    # remise effective ≥ 50 %
_DISCOUNT_EFFECT_MEDIUM = Decimal("-30")  # remise effective ≥ 30 %


def _to_decimal(value: object) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value))


def _round_decimal(value: Decimal, places: str = "0.01") -> Decimal:
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)


def _uplift_severity(uplift_rate: Decimal, family_effect_flag: str | None) -> str:
    """
    Détermine la sévérité d'une promo sous-performante.

    La cannibalization aggrave la sévérité d'un cran :
    une promo MEDIUM avec CANNIBALIZATION devient HIGH.
    """
    if uplift_rate <= _UPLIFT_HIGH:
        return "HIGH"

    if uplift_rate <= _UPLIFT_MEDIUM or family_effect_flag == "CANNIBALIZATION":
        return "HIGH" if family_effect_flag == "CANNIBALIZATION" and uplift_rate <= _UPLIFT_MEDIUM else "MEDIUM"

    return "LOW"


def _discount_severity(discount_effect_pct: Decimal) -> str:
    if discount_effect_pct <= _DISCOUNT_EFFECT_HIGH:
        return "HIGH"
    if discount_effect_pct <= _DISCOUNT_EFFECT_MEDIUM:
        return "MEDIUM"
    return "LOW"


def _family_name_by_id(db: Session, family_id: int) -> str | None:
    row = db.execute(
        select(ProductFamily.name).where(ProductFamily.id == family_id)
    ).scalar_one_or_none()
    return row


def _quota_per_severity(limit: int) -> dict[str, int]:
    """
    Répartit le quota total entre les 3 niveaux de sévérité.
    HIGH reçoit la moitié, MEDIUM et LOW se partagent le reste.
    Garantit qu'au moins 1 résultat par sévérité est retourné si possible.
    """
    high = max(limit // 2, 1)
    medium = max((limit - high) // 2, 1)
    low = max(limit - high - medium, 1)
    return {"HIGH": high, "MEDIUM": medium, "LOW": low}


def _get_underperforming_promos(
    db: Session,
    promotion_id: int | None,
    product_id: int | None,
    store_id: int | None,
    limit: int,
) -> list[BusinessAnomalyRead]:
    """
    Détecte les promotions dont le CA quotidien est inférieur
    au CA quotidien du même produit 14 jours avant la promotion.

    Source : pct_analytics.kpi_promo_performance (mart dbt)
    Baseline : fenêtre de 14 jours précédant le début de la promotion,
               normalisée en moyenne journalière pour neutraliser les
               différences de durée entre promo et baseline.

    Critère d'entrée : revenue_uplift_rate < -10 %
    (= la promo génère moins de CA par jour qu'avant la promo)

    Sévérité :
    - LOW    : uplift entre -10 % et -30 %
    - MEDIUM : uplift ≤ -30 %, ou uplift négatif avec CANNIBALIZATION
    - HIGH   : uplift ≤ -50 %, ou uplift ≤ -30 % avec CANNIBALIZATION

    Les promotions NOT_COMPARABLE (nouveau produit, pas de baseline)
    sont exclues — elles sont traitées via la règle INEFFECTIVE_DISCOUNT.
    """
    def _base_query():
        q = (
            select(KpiPromoPerformance)
            .where(KpiPromoPerformance.promo_performance_flag != "NOT_COMPARABLE")
            .where(KpiPromoPerformance.revenue_uplift_rate.is_not(None))
        )
        if promotion_id is not None:
            q = q.where(KpiPromoPerformance.promotion_id == promotion_id)
        if product_id is not None:
            q = q.where(KpiPromoPerformance.product_id == product_id)
        if store_id is not None:
            q = q.where(KpiPromoPerformance.store_id == store_id)
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
            " De plus, les autres produits de la famille ont subi une baisse de CA (effet de cannibalisation)."
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
                    f"CA total promo : {promo_revenue} € vs {expected_revenue} € attendu.{cannibal_note}"
                ),
                promotion_id=row.promotion_id,
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


def _get_ineffective_discount_promos(
    db: Session,
    promotion_id: int | None,
    product_id: int | None,
    store_id: int | None,
    limit: int,
) -> list[BusinessAnomalyRead]:
    """
    Détecte les promotions avec une remise effective significative
    mais sans uplift de volume (on sacrifie de la marge sans vendre plus).

    Critères :
    - avg_price_discount_effect_pct ≤ -20 % (le prix a baissé d'au moins 20 %)
    - quantity_uplift_rate ≤ 0 (le volume n'a pas augmenté)

    Couvre aussi les nouveaux produits (NOT_COMPARABLE) si la remise
    dépasse 50 % par rapport au prix de référence — cas probable d'erreur de saisie.

    Sévérité :
    - LOW    : remise effective entre -20 % et -30 %
    - MEDIUM : remise effective entre -30 % et -50 %
    - HIGH   : remise effective ≥ 50 %
    """
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
        if promotion_id is not None:
            q = q.where(KpiPromoPerformance.promotion_id == promotion_id)
        if product_id is not None:
            q = q.where(KpiPromoPerformance.product_id == product_id)
        if store_id is not None:
            q = q.where(KpiPromoPerformance.store_id == store_id)
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
            else f"Le volume vendu n'a pas augmenté malgré la remise (uplift quantité : {_round_decimal(_to_decimal(row.quantity_uplift_rate) * 100, '0.1')} %)."
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


def get_business_anomalies(
    db: Session,
    promotion_id: int | None = None,
    product_id: int | None = None,
    store_id: int | None = None,
    limit: int = 50,
) -> list[BusinessAnomalyRead]:
    """
    Détecte les anomalies tarifaires et commerciales depuis pct_analytics.kpi_promo_performance.

    Chaque promotion est comparée à elle-même sur les 14 jours précédant son démarrage.
    Cette approche intra-produit élimine le biais lié aux différences de prix entre produits
    et évite la contamination des statistiques par les anomalies elles-mêmes.

    Deux règles sont appliquées :

    1. UNDERPERFORMING_PROMO
       La promotion génère moins de CA par jour qu'avant son démarrage (uplift négatif).
       → Détecte les promotions qui détruisent de la valeur sans attirer de clients.
       Sévérité :
       - LOW    : CA en baisse de 10 % à 30 %
       - MEDIUM : CA en baisse ≥ 30 %, ou baisse + cannibalisation de la famille
       - HIGH   : CA en baisse ≥ 50 %, ou baisse ≥ 30 % + cannibalisation

    2. INEFFECTIVE_DISCOUNT
       La remise réduit le prix de vente de ≥ 20 % sans générer d'uplift de volume.
       → Détecte les promotions où on sacrifie de la marge sans bénéfice commercial.
       Couvre aussi les erreurs de remise sur les nouveaux produits (pas de baseline).
       Sévérité :
       - LOW    : remise effective 20 % à 30 %
       - MEDIUM : remise effective 30 % à 50 %
       - HIGH   : remise effective ≥ 50 %
    """
    underperforming = _get_underperforming_promos(
        db=db,
        promotion_id=promotion_id,
        product_id=product_id,
        store_id=store_id,
        limit=limit,
    )
    ineffective = _get_ineffective_discount_promos(
        db=db,
        promotion_id=promotion_id,
        product_id=product_id,
        store_id=store_id,
        limit=limit,
    )

    return (underperforming + ineffective)[:limit]
