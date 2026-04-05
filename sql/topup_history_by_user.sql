SELECT
    t.id,
    c.full_name,
    u.username,
    t.amount,
    t.note,
    t.status
FROM accounts_topuprequest t
JOIN accounts_customer c ON c.id = t.customer_id
JOIN auth_user u ON u.id = c.user_id
WHERE u.id = %s
ORDER BY t.id DESC
LIMIT %s;
