with sales_enriched as (

    select * from {{ ref('int_sales_enriched') }}

),

product_families as (

    select * from {{ ref('stg_product_family') }}

),

countries as (

    select * from {{ ref('stg_country') }}

),

obt as (

    select
        -- Transaction
        se.transaction_id,
        se.transaction_date,
        cast(se.transaction_date as date)                as transaction_day,
        date_trunc('month', se.transaction_date)::date   as transaction_month,

        -- Product
        se.product_id,
        se.product_code,
        se.product_name,
        se.brand,
        se.model,
        pf.product_family_id,
        pf.product_family_code,
        pf.product_family_name,

        -- Store & Geography
        se.store_id,
        se.store_code,
        se.store_name,
        se.city,
        se.region,
        c.country_id,
        c.country_code,
        c.country_name,

        -- Price
        se.price_id,
        se.price_amount,
        se.currency_code,
        se.price_effective_from,
        se.price_effective_to,
        se.price_status,
        se.price_scope,
        se.price_type,

        -- Promotion
        se.promotion_id,
        se.promotion_code,
        se.promotion_name,
        se.discount_type,
        se.discount_value,
        se.promotion_start_date,
        se.promotion_end_date,
        se.is_promo,

        -- Measures
        se.quantity,
        se.unit_price,
        se.revenue

    from sales_enriched se
    left join product_families pf on se.product_family_id = pf.product_family_id
    left join countries c         on se.country_id        = c.country_id

)

select * from obt
