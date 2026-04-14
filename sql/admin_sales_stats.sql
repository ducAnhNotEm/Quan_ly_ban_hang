SELECT
    (SELECT COUNT(*) FROM accounts_customer) AS customer_count,
    (SELECT COUNT(*) FROM orders_order WHERE status = 'PAID') AS order_count,
    (SELECT COUNT(*) FROM products_product) AS product_count,
    COALESCE(
        (SELECT SUM(total_amount) FROM orders_order WHERE status = 'PAID'),
        0
    ) AS total_revenue;
