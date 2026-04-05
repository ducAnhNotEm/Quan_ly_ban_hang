SELECT
    id
FROM auth_user
WHERE LOWER(username) = LOWER(%s)
LIMIT 1;
