{{ config(materialized='table') }}

with sales as (

    select
        transaction_date::date as transaction_date,
        country_id,
        store_id,
        product_id,
        quantity,
        revenue,
        is_promo
    from {{ ref('obt_sales') }}
    where quantity > 0
      and revenue > 0

),

date_bounds as (

    select
        max(transaction_date) as max_transaction_date
    from sales

),

period_bounds as (

    select
        max_transaction_date,
        max_transaction_date - interval '30 days' as current_period_start_date,
        max_transaction_date as current_period_end_date,
        max_transaction_date - interval '60 days' as previous_period_start_date,
        max_transaction_date - interval '30 days' as previous_period_end_date,
        30 as analysis_period_days
    from date_bounds

),

periodized_sales as (

    select
        s.*,
        p.analysis_period_days,
        p.current_period_start_date,
        p.current_period_end_date,
        p.previous_period_start_date,
        p.previous_period_end_date,
        case
            when s.transaction_date > p.current_period_start_date
             and s.transaction_date <= p.current_period_end_date
                then 'current_period'
            when s.transaction_date > p.previous_period_start_date
             and s.transaction_date <= p.previous_period_end_date
                then 'previous_period'
            else 'out_of_scope'
        end as analysis_period
    from sales s
    cross join period_bounds p

),

aggregated as (

    select
        country_id,
        store_id,
        product_id,

        max(analysis_period_days) as analysis_period_days,
        max(current_period_start_date)::date as current_period_start_date,
        max(current_period_end_date)::date as current_period_end_date,
        max(previous_period_start_date)::date as previous_period_start_date,
        max(previous_period_end_date)::date as previous_period_end_date,

        sum(case when analysis_period = 'current_period' then revenue else 0 end) as current_revenue,
        sum(case when analysis_period = 'previous_period' then revenue else 0 end) as previous_revenue,

        sum(case when analysis_period = 'current_period' then quantity else 0 end) as current_quantity,
        sum(case when analysis_period = 'previous_period' then quantity else 0 end) as previous_quantity,

        sum(case when analysis_period = 'current_period' and is_promo then revenue else 0 end) as current_promo_revenue

    from periodized_sales
    where analysis_period in ('current_period', 'previous_period')
    group by
        country_id,
        store_id,
        product_id

),

country_benchmark as (

    select
        country_id,
        product_id,

        sum(case when analysis_period = 'current_period' then revenue else 0 end) as country_current_revenue,
        sum(case when analysis_period = 'current_period' then quantity else 0 end) as country_current_quantity,

        count(distinct case when analysis_period = 'current_period' then store_id end) as country_store_count,

        sum(case when analysis_period = 'current_period' then revenue else 0 end)
            / nullif(sum(case when analysis_period = 'current_period' then quantity else 0 end), 0)
            as country_avg_selling_price

    from periodized_sales
    where analysis_period = 'current_period'
    group by
        country_id,
        product_id

),

final as (

    select
        a.country_id,
        a.store_id,
        a.product_id,

        a.analysis_period_days,
        a.current_period_start_date,
        a.current_period_end_date,
        a.previous_period_start_date,
        a.previous_period_end_date,

        a.current_revenue,
        a.previous_revenue,

        case
            when a.previous_revenue = 0 then null
            else round(((a.current_revenue - a.previous_revenue) / a.previous_revenue) * 100, 2)
        end as revenue_change_pct,

        a.current_quantity,
        a.previous_quantity,

        case
            when a.previous_quantity = 0 then null
            else round(((a.current_quantity - a.previous_quantity)::numeric / a.previous_quantity) * 100, 2)
        end as quantity_change_pct,

        round(a.current_revenue / nullif(a.current_quantity, 0), 2) as current_avg_selling_price,
        round(a.previous_revenue / nullif(a.previous_quantity, 0), 2) as previous_avg_selling_price,

        case
            when a.previous_quantity = 0 or a.previous_revenue = 0 then null
            else round(
                (
                    ((a.current_revenue / nullif(a.current_quantity, 0))
                    - (a.previous_revenue / nullif(a.previous_quantity, 0)))
                    / nullif((a.previous_revenue / nullif(a.previous_quantity, 0)), 0)
                ) * 100,
                2
            )
        end as avg_price_change_pct,

        cb.country_current_revenue,
        cb.country_current_quantity,
        cb.country_store_count,

        round(cb.country_avg_selling_price, 2) as country_avg_selling_price,

        case
            when cb.country_avg_selling_price = 0 then null
            else round(
                (
                    (a.current_revenue / nullif(a.current_quantity, 0))
                    - cb.country_avg_selling_price
                ) / cb.country_avg_selling_price * 100,
                2
            )
        end as price_vs_country_benchmark_pct,

        case
            when a.current_revenue = 0 then null
            else round((a.current_promo_revenue / a.current_revenue) * 100, 2)
        end as current_promo_revenue_share

    from aggregated a
    left join country_benchmark cb
        on a.country_id = cb.country_id
       and a.product_id = cb.product_id

)

select
    *,

    case
        when previous_revenue = 0 and current_revenue > 0 then 'NEW_ACTIVITY'
        when revenue_change_pct >= 20 then 'STRONG_GROWTH'
        when revenue_change_pct <= -20 then 'STRONG_DECLINE'
        when revenue_change_pct between -20 and 20 then 'STABLE'
        else 'NOT_COMPARABLE'
    end as performance_flag,

    case
        when current_avg_selling_price is null
        or country_avg_selling_price is null
            then 'NOT_COMPARABLE'
        when round(current_avg_selling_price, 2) = round(country_avg_selling_price, 2)
            then 'ALIGNED_WITH_COUNTRY_BENCHMARK'
        when round(current_avg_selling_price, 2) > round(country_avg_selling_price, 2)
            then 'ABOVE_COUNTRY_BENCHMARK'
        when round(current_avg_selling_price, 2) < round(country_avg_selling_price, 2)
            then 'BELOW_COUNTRY_BENCHMARK'
        else 'NOT_COMPARABLE'
    end as benchmark_flag

from final
