with cleaned_orders as (
    select *,
           quantity * unit_price as line_total
    from {{ ref('int_order_lines_cleaned') }}
),

customer_aggregates as (
    select
        customer_id,
        max(invoice_date) as last_order_date,
        count(distinct invoice_no) as frequency,
        sum(line_total) as monetary_value
    from cleaned_orders
    group by customer_id
),

global_max_date as (
    select max(invoice_date) as max_date
    from cleaned_orders
),

rfm_calculated as (
    select
        c.customer_id,
        -- Calculate Recency as the difference in days from the most recent order in the dataset
        date_diff('day', c.last_order_date, g.max_date) as recency,
        c.frequency,
        c.monetary_value
    from customer_aggregates c
    cross join global_max_date g
)

select * from rfm_calculated
