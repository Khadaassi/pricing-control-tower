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

        -- Pricing information captured on the transaction
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

        -- Referenced price record
        pr.price_id,
        pr.price_amount,
        pr.currency_code,
        pr.effective_from as price_effective_from,
        pr.effective_to as price_effective_to,
        pr.price_status,

        -- Price analysis fields
        s.unit_price - pr.price_amount as price_difference,

        case
            when pr.price_amount is not null
             and pr.price_amount != 0
            then round(
                ((s.unit_price - pr.price_amount) / pr.price_amount)::numeric,
                4
            )
            else null
        end as price_difference_rate,

        case
            when s.price_scope = 'STORE' then true
            else false
        end as is_store_specific_price,

        case
            when s.price_type = 'PROMO' then true
            else false
        end as is_promotional_price,

        case
            when cast(s.transaction_date as date) >= pr.effective_from
             and (
                pr.effective_to is null
                or cast(s.transaction_date as date) <= pr.effective_to
             )
            then true
            else false
        end as is_price_temporally_valid,

        -- Promotion
        promo.promotion_id,
        promo.promotion_code,
        promo.promotion_name,
        promo.discount_type,
        promo.discount_value,
        promo.promotion_start_date,
        promo.promotion_end_date

    from sales s

    left join products p
        on s.product_id = p.product_id

    left join stores st
        on s.store_id = st.store_id

    left join prices pr
        on s.price_id = pr.price_id

    left join promotions promo
        on s.promotion_id = promo.promotion_id

)

select * from enriched