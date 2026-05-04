with source as (

    select * from {{ source('pct_core', 'product_family') }}

),

renamed as (

    select
        id          as product_family_id,
        code        as product_family_code,
        name        as product_family_name,
        description as product_family_description

    from source

)

select * from renamed
