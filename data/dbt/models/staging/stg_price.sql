with source as (

    select * from {{ source('pct_core', 'price') }}

),

renamed as (

    select
        id              as price_id,
        product_id,
        price_scope,
        country_id,
        store_id,
        price_type,
        amount          as price_amount,
        currency_code,
        effective_from,
        effective_to,
        status          as price_status,
        promotion_id,
        reason,
        created_by,
        created_at

    from source

)

select * from renamed
