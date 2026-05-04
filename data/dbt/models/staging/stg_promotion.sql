with source as (

    select * from {{ source('pct_core', 'promotion') }}

),

renamed as (

    select
        id              as promotion_id,
        code            as promotion_code,
        name            as promotion_name,
        description     as promotion_description,
        discount_type,
        discount_value,
        start_date,
        end_date,
        country_id,
        store_id,
        created_by,
        created_at,
        active          as is_active

    from source

)

select * from renamed
