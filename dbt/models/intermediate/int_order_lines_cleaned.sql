with orders as (
    select * from {{ ref('stg_orders') }}
),

cleaned as (
    select *
    from orders
    where 
        customer_id is not null
        and quantity > 0
        and unit_price > 0
        and (invoice_no not like 'C%' or invoice_no is null)
),

deduped as (
    select distinct *
    from cleaned
)

select * from deduped
