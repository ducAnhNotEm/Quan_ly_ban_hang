SELECT
    id,
    username,
    email,
    is_active,
    is_staff
FROM auth_user
WHERE username = %s
LIMIT 1;
