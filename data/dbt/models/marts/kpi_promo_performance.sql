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
        quantity,
        revenue,
        is_promo
    from {{ ref('obt_sales') }}
    where quantity > 0
      and revenue > 0

),

promo_sales as (

    select
        country_id,
        store_id,
        product_id,
        product_family_id,
        promotion_id,
        promotion_start_date,
        promotion_end_date,

        (promotion_start_date - interval '14 days')::date as baseline_start_date,
        (promotion_start_date - interval '1 day')::date as baseline_end_date,

        count(distinct transaction_date) as promo_days_observed,

        greatest(
            (promotion_end_date - promotion_start_date + 1),
            1
        ) as promo_period_days,

        sum(quantity) as promo_quantity,
        sum(revenue) as promo_revenue,

        sum(revenue) / nullif(sum(quantity), 0) as promo_avg_selling_price

    from sales
    where is_promo = true
      and promotion_id is not null
      and transaction_date between promotion_start_date and promotion_end_date
    group by
        country_id,
        store_id,
        product_id,
        product_family_id,
        promotion_id,
        promotion_start_date,
        promotion_end_date

),

baseline_sales as (

    select
        p.country_id,
        p.store_id,
        p.product_id,
        p.product_family_id,
        p.promotion_id,

        count(distinct s.transaction_date) as baseline_days_observed,

        sum(s.quantity) as baseline_quantity,
        sum(s.revenue) as baseline_revenue,

        sum(s.revenue) / nullif(sum(s.quantity), 0) as baseline_avg_selling_price

    from promo_sales p
    left join sales s
        on s.country_id = p.country_id
       and s.store_id = p.store_id
       and s.product_family_id = p.product_family_id
       and s.product_id <> p.product_id
       and s.is_promo = false
       and s.transaction_date >= p.baseline_start_date
       and s.transaction_date <= p.baseline_end_date
    group by
        p.country_id,
        p.store_id,
        p.product_id,
        p.product_family_id,
        p.promotion_id

),

calculated as (

    select
        p.country_id,
        p.store_id,
        p.product_id,
        p.product_family_id,
        p.promotion_id,

        p.promotion_start_date,
        p.promotion_end_date,

        p.baseline_start_date,
        p.baseline_end_date,

        p.promo_days_observed,
        p.promo_period_days,

        p.promo_quantity,
        p.promo_revenue,
        round(p.promo_avg_selling_price, 2) as promo_avg_selling_price,

        coalesce(b.baseline_days_observed, 0) as baseline_days_observed,
        14 as baseline_period_days,

        coalesce(b.baseline_quantity, 0) as baseline_quantity,
        coalesce(b.baseline_revenue, 0) as baseline_revenue,
        round(b.baseline_avg_selling_price, 2) as baseline_avg_selling_price,

        round(
            p.promo_quantity::numeric / nullif(p.promo_period_days, 0),
            2
        ) as promo_daily_quantity,

        round(
            p.promo_revenue / nullif(p.promo_period_days, 0),
            2
        ) as promo_daily_revenue,

        round(
            coalesce(b.baseline_quantity, 0)::numeric / 14,
            2
        ) as baseline_daily_quantity,

        round(
            coalesce(b.baseline_revenue, 0) / 14,
            2
        ) as baseline_daily_revenue

    from promo_sales p
    left join baseline_sales b
        on p.country_id = b.country_id
       and p.store_id = b.store_id
       and p.product_id = b.product_id
       and p.product_family_id = b.product_family_id
       and p.promotion_id = b.promotion_id

),

uplift as (

    select
        *,

        case
            when baseline_daily_quantity = 0 then null
            else round(
                (promo_daily_quantity - baseline_daily_quantity)
                / nullif(baseline_daily_quantity, 0),
                4
            )
        end as quantity_uplift_rate,

        case
            when baseline_daily_quantity = 0 then null
            else round(
                (
                    (promo_daily_quantity - baseline_daily_quantity)
                    / nullif(baseline_daily_quantity, 0)
                ) * 100,
                2
            )
        end as quantity_uplift_pct,

        case
            when baseline_daily_quantity = 0 then null
            else round(
                promo_quantity::numeric
                - (baseline_daily_quantity * promo_period_days),
                2
            )
        end as additional_quantity,

        case
            when baseline_daily_revenue = 0 then null
            else round(
                (promo_daily_revenue - baseline_daily_revenue)
                / nullif(baseline_daily_revenue, 0),
                4
            )
        end as revenue_uplift_rate,

        case
            when baseline_daily_revenue = 0 then null
            else round(
                (
                    (promo_daily_revenue - baseline_daily_revenue)
                    / nullif(baseline_daily_revenue, 0)
                ) * 100,
                2
            )
        end as revenue_uplift_pct,

        case
            when baseline_daily_revenue = 0 then null
            else round(
                promo_revenue
                - (baseline_daily_revenue * promo_period_days),
                2
            )
        end as additional_revenue,

        case
            when baseline_avg_selling_price is null
              or baseline_avg_selling_price = 0 then null
            else round(
                (
                    promo_avg_selling_price - baseline_avg_selling_price
                )
                / baseline_avg_selling_price
                * 100,
                2
            )
        end as avg_price_discount_effect_pct

    from calculated

)

select
    *,

    case
        when baseline_quantity = 0
          or baseline_revenue = 0
            then 'NOT_COMPARABLE'

        when quantity_uplift_rate > 0
         and revenue_uplift_rate > 0
            then 'EFFICIENT_PROMO'

        when quantity_uplift_rate > 0
         and revenue_uplift_rate <= 0
            then 'VOLUME_ONLY_PROMO'

        when quantity_uplift_rate <= 0
         and revenue_uplift_rate < 0
            then 'UNDERPERFORMING_PROMO'

        else 'MIXED_PERFORMANCE'
    end as promo_performance_flag

from uplift
