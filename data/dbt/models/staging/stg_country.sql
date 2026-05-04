with source as (

    select * from {{ source('pct_core', 'country') }}

),

renamed as (

    select
        id   as country_id,
        code as country_code,
        name as country_name

    from source

)

select * from renamed
