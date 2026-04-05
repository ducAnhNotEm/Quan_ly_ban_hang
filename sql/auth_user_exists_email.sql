SELECT
    id
FROM auth_user
WHERE LOWER(email) = LOWER(%s)
LIMIT 1;
