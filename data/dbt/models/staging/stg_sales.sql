with source as (

    select * from {{ source('pct_core', 'sales_transaction') }}

),

renamed as (

    select
        transaction_id,
        transaction_date,
        product_id,
        store_id,
        price_id,
        promotion_id,
        quantity,
        unit_price,
        revenue,
        is_promo,
        price_scope,
        price_type

    from source

)

select * from renamed
