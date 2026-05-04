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

        start_date      as promotion_start_date,
        end_date        as promotion_end_date,

        country_id      as promotion_country_id,
        store_id        as promotion_store_id,

        created_by      as promotion_created_by,
        created_at      as promotion_created_at,

        active          as promotion_is_active

    from source

)

select * from renamed
