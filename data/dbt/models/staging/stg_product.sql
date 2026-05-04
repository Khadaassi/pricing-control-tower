with source as (

    select * from {{ source('pct_core', 'product') }}

),

renamed as (

    select
        id          as product_id,
        code        as product_code,
        name        as product_name,
        description as product_description,
        brand,
        model,
        active      as is_active,
        product_family_id

    from source

)

select * from renamed
