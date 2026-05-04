with source as (

    select * from {{ source('pct_core', 'store') }}

),

renamed as (

    select
        id           as store_id,
        code         as store_code,
        name         as store_name,
        country_id,
        city,
        region,
        opening_date

    from source

)

select * from renamed
