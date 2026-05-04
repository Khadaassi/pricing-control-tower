with sales as (

    select * from {{ ref('stg_sales') }}

),

products as (

    select * from {{ ref('stg_product') }}

),

stores as (

    select * from {{ ref('stg_store') }}

),

prices as (

    select * from {{ ref('stg_price') }}

),

promotions as (

    select * from {{ ref('stg_promotion') }}

),

enriched as (

    select
        -- Sale
        s.transaction_id,
        s.transaction_date,
        s.quantity,
        s.unit_price,
        s.revenue,
        s.is_promo,
        s.price_scope,
        s.price_type,

        -- Product
        p.product_id,
        p.product_code,
        p.product_name,
        p.brand,
        p.model,
        p.product_family_id,

        -- Store
        st.store_id,
        st.store_code,
        st.store_name,
        st.country_id,
        st.city,
        st.region,

        -- Price
        pr.price_id,
        pr.price_amount,
        pr.currency_code,
        pr.effective_from   as price_effective_from,
        pr.effective_to     as price_effective_to,
        pr.price_status,

        -- Promotion
        promo.promotion_id,
        promo.promotion_code,
        promo.promotion_name,
        promo.discount_type,
        promo.discount_value,
        promo.start_date    as promotion_start_date,
        promo.end_date      as promotion_end_date

    from sales s
    left join products p    on s.product_id   = p.product_id
    left join stores st     on s.store_id     = st.store_id
    left join prices pr     on s.price_id     = pr.price_id
    left join promotions promo on s.promotion_id = promo.promotion_id

)

select * from enriched
