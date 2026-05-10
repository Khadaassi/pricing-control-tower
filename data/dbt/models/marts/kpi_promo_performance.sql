{{ config(materialized='table') }}

-- =============================================================================
-- Promotion Performance KPI
--
-- Business rules:
--   1. Primary uplift is computed at PRODUCT level only
--      (same product BEFORE promo vs DURING promo).
--   2. Product family is NEVER used to compute the primary uplift.
--   3. A secondary family-level indicator detects cannibalization / halo effect.
--   4. All comparisons are normalized to daily averages to account for
--      differences in promo duration vs baseline period (14 days).
-- =============================================================================

with sales as (

    select
        transaction_date::date as transaction_date,
        country_id,
        store_id,
        product_id,
        product_family_id,
        promotion_id,
        promotion_start_date::date as promotion_start_date,
        promotion_end_date::date as promotion_end_date,
        discount_type,
        discount_value,
        quantity,
        revenue,
        is_promo
    from {{ ref('obt_sales') }}
    where quantity > 0
      and revenue > 0

),

-- Product sales DURING the promotion period
promo_sales as (

    select
        country_id,
        store_id,
        product_id,
        product_family_id,
        promotion_id,
        promotion_start_date,
        promotion_end_date,
        discount_type,
        discount_value,

        (promotion_start_date - interval '14 days')::date as baseline_start_date,
        (promotion_start_date - interval '1 day')::date   as baseline_end_date,

        count(distinct transaction_date) as promo_days_observed,

        greatest(
            (promotion_end_date - promotion_start_date + 1),
            1
        ) as promo_period_days,

        sum(quantity) as promo_quantity,
        sum(revenue)  as promo_revenue,
        sum(revenue) / nullif(sum(quantity), 0) as promo_avg_selling_price

    from sales
    where is_promo = true
      and promotion_id is not null
      and transaction_date between promotion_start_date and promotion_end_date
    group by
        country_id, store_id, product_id, product_family_id,
        promotion_id, promotion_start_date, promotion_end_date,
        discount_type, discount_value

),

-- Same product sales BEFORE the promotion (14-day baseline window)
baseline_sales as (

    select
        p.country_id,
        p.store_id,
        p.product_id,
        p.promotion_id,

        count(distinct s.transaction_date) as baseline_days_observed,
        sum(s.quantity) as baseline_quantity,
        sum(s.revenue)  as baseline_revenue,
        sum(s.revenue) / nullif(sum(s.quantity), 0) as baseline_avg_selling_price

    from promo_sales p
    left join sales s
        on  s.country_id = p.country_id
        and s.store_id   = p.store_id
        and s.product_id = p.product_id
        and s.is_promo   = false
        and s.transaction_date >= p.baseline_start_date
        and s.transaction_date <= p.baseline_end_date
    group by
        p.country_id, p.store_id, p.product_id, p.promotion_id

),

-- Other products in the same family DURING the promotion (for halo / cannibalization)
family_during_promo as (

    select
        p.country_id,
        p.store_id,
        p.product_id,
        p.product_family_id,
        p.promotion_id,

        sum(s.quantity) as family_promo_quantity,
        sum(s.revenue)  as family_promo_revenue

    from promo_sales p
    left join sales s
        on  s.country_id        = p.country_id
        and s.store_id          = p.store_id
        and s.product_family_id = p.product_family_id
        and s.product_id       <> p.product_id
        and s.transaction_date  >= p.promotion_start_date
        and s.transaction_date  <= p.promotion_end_date
    group by
        p.country_id, p.store_id, p.product_id,
        p.product_family_id, p.promotion_id

),

-- Other products in the same family BEFORE the promotion (baseline for family KPI)
family_before_promo as (

    select
        p.country_id,
        p.store_id,
        p.product_id,
        p.product_family_id,
        p.promotion_id,

        sum(s.quantity) as family_baseline_quantity,
        sum(s.revenue)  as family_baseline_revenue

    from promo_sales p
    left join sales s
        on  s.country_id        = p.country_id
        and s.store_id          = p.store_id
        and s.product_family_id = p.product_family_id
        and s.product_id       <> p.product_id
        and s.is_promo          = false
        and s.transaction_date  >= p.baseline_start_date
        and s.transaction_date  <= p.baseline_end_date
    group by
        p.country_id, p.store_id, p.product_id,
        p.product_family_id, p.promotion_id

),

-- Assemble all metrics and normalize to daily averages
calculated as (

    select
        p.country_id,
        p.store_id,
        p.product_id,
        p.product_family_id,
        p.promotion_id,
        p.discount_type,
        p.discount_value,

        p.promotion_start_date,
        p.promotion_end_date,
        p.baseline_start_date,
        p.baseline_end_date,

        p.promo_days_observed,
        p.promo_period_days,
        14 as baseline_period_days,

        -- Product totals
        p.promo_quantity,
        p.promo_revenue,
        round(p.promo_avg_selling_price, 2) as promo_avg_selling_price,

        coalesce(b.baseline_days_observed, 0) as baseline_days_observed,
        coalesce(b.baseline_quantity, 0)      as baseline_quantity,
        coalesce(b.baseline_revenue, 0)       as baseline_revenue,
        round(b.baseline_avg_selling_price, 2) as baseline_avg_selling_price,

        -- Product daily averages
        round(p.promo_quantity::numeric / nullif(p.promo_period_days, 0), 2) as promo_daily_quantity,
        round(p.promo_revenue / nullif(p.promo_period_days, 0), 2)          as promo_daily_revenue,
        round(coalesce(b.baseline_quantity, 0)::numeric / 14, 2)            as baseline_daily_quantity,
        round(coalesce(b.baseline_revenue, 0) / 14, 2)                      as baseline_daily_revenue,

        -- Family totals
        coalesce(fd.family_promo_quantity, 0)    as family_promo_quantity,
        coalesce(fd.family_promo_revenue, 0)     as family_promo_revenue,
        coalesce(fb.family_baseline_quantity, 0) as family_baseline_quantity,
        coalesce(fb.family_baseline_revenue, 0)  as family_baseline_revenue,

        -- Family daily averages (normalized like the product KPI)
        round(coalesce(fd.family_promo_quantity, 0)::numeric / nullif(p.promo_period_days, 0), 2) as family_promo_daily_quantity,
        round(coalesce(fd.family_promo_revenue, 0) / nullif(p.promo_period_days, 0), 2)          as family_promo_daily_revenue,
        round(coalesce(fb.family_baseline_quantity, 0)::numeric / 14, 2)                         as family_baseline_daily_quantity,
        round(coalesce(fb.family_baseline_revenue, 0) / 14, 2)                                   as family_baseline_daily_revenue

    from promo_sales p
    left join baseline_sales b
        on  p.country_id  = b.country_id
        and p.store_id    = b.store_id
        and p.product_id  = b.product_id
        and p.promotion_id = b.promotion_id
    left join family_during_promo fd
        on  p.country_id  = fd.country_id
        and p.store_id    = fd.store_id
        and p.product_id  = fd.product_id
        and p.promotion_id = fd.promotion_id
    left join family_before_promo fb
        on  p.country_id  = fb.country_id
        and p.store_id    = fb.store_id
        and p.product_id  = fb.product_id
        and p.promotion_id = fb.promotion_id

),

-- Compute uplift rates and family effect indicators
uplift as (

    select
        *,

        -- Primary KPI: product-level uplift (daily comparison)
        case when baseline_daily_quantity = 0 then null else round(
            (promo_daily_quantity - baseline_daily_quantity) / baseline_daily_quantity, 4
        ) end as quantity_uplift_rate,

        case when baseline_daily_quantity = 0 then null else round(
            ((promo_daily_quantity - baseline_daily_quantity) / baseline_daily_quantity) * 100, 2
        ) end as quantity_uplift_pct,

        case when baseline_daily_quantity = 0 then null else round(
            promo_quantity::numeric - (baseline_daily_quantity * promo_period_days), 2
        ) end as additional_quantity,

        case when baseline_daily_revenue = 0 then null else round(
            (promo_daily_revenue - baseline_daily_revenue) / baseline_daily_revenue, 4
        ) end as revenue_uplift_rate,

        case when baseline_daily_revenue = 0 then null else round(
            ((promo_daily_revenue - baseline_daily_revenue) / baseline_daily_revenue) * 100, 2
        ) end as revenue_uplift_pct,

        case when baseline_daily_revenue = 0 then null else round(
            promo_revenue - (baseline_daily_revenue * promo_period_days), 2
        ) end as additional_revenue,

        case
            when baseline_avg_selling_price is null or baseline_avg_selling_price = 0 then null
            else round(
                (promo_avg_selling_price - baseline_avg_selling_price)
                / baseline_avg_selling_price * 100, 2
            )
        end as avg_price_discount_effect_pct,

        -- Secondary KPI: family-level variation (daily comparison)
        case when family_baseline_daily_quantity = 0 then null else round(
            ((family_promo_daily_quantity - family_baseline_daily_quantity)
             / family_baseline_daily_quantity) * 100, 2
        ) end as family_quantity_variation_pct,

        case when family_baseline_daily_revenue = 0 then null else round(
            ((family_promo_daily_revenue - family_baseline_daily_revenue)
             / family_baseline_daily_revenue) * 100, 2
        ) end as family_revenue_variation_pct,

        case
            when family_baseline_daily_quantity = 0 then 'NO_FAMILY_DATA'
            when (family_promo_daily_quantity - family_baseline_daily_quantity)
                 / nullif(family_baseline_daily_quantity, 0) < -0.10
                then 'CANNIBALIZATION'
            when (family_promo_daily_quantity - family_baseline_daily_quantity)
                 / nullif(family_baseline_daily_quantity, 0) > 0.10
                then 'HALO_EFFECT'
            else 'NEUTRAL'
        end as family_effect_flag

    from calculated

)

select
    *,

    case
        when baseline_quantity = 0 or baseline_revenue = 0 then 'NOT_COMPARABLE'
        when quantity_uplift_rate > 0 and revenue_uplift_rate > 0 then 'EFFICIENT_PROMO'
        when quantity_uplift_rate > 0 and revenue_uplift_rate <= 0 then 'VOLUME_ONLY_PROMO'
        when quantity_uplift_rate <= 0 and revenue_uplift_rate < 0 then 'UNDERPERFORMING_PROMO'
        else 'MIXED_PERFORMANCE'
    end as promo_performance_flag

from uplift
