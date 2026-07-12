with source as (
    select * from {{ source('retail', 'raw_orders') }}
),

renamed as (
    select
        coalesce(invoice_no__v_text, cast(invoice_no as varchar)) as invoice_no,
        cast(stock_code as varchar) as stock_code,
        cast(description as varchar) as description,
        cast(quantity as integer) as quantity,
        cast(invoice_date as timestamp) as invoice_date,
        cast(unit_price as numeric) as unit_price,
        cast(customer_id as integer) as customer_id,
        cast(country as varchar) as country
    from source
)

select * from renamed
