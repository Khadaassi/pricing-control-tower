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

periodized_sales as (

    select
        s.*,
        case
            when s.transaction_date > d.max_transaction_date - interval '30 days'
                then 'current_period'
            when s.transaction_date > d.max_transaction_date - interval '60 days'
             and s.transaction_date <= d.max_transaction_date - interval '30 days'
                then 'previous_period'
            else 'out_of_scope'
        end as analysis_period
    from sales s
    cross join date_bounds d

),

aggregated as (

    select
        country_id,
        store_id,
        product_id,

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
        sum(revenue) / nullif(sum(quantity), 0) as country_avg_selling_price
    from periodized_sales
    where analysis_period = 'current_period'
    group by
        country_id,
        product_id

)

select
    a.country_id,
    a.store_id,
    a.product_id,

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
