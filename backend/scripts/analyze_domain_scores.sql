
-- Get per-user domain scores and their personal Min/Max across domains
-- This helps understand the "spread" of a user's interests.

SELECT
    user_id,
    (domain_scores->>'sensation')::int as sensation,
    (domain_scores->>'connection')::int as connection,
    (domain_scores->>'power')::int as power,
    (domain_scores->>'exploration')::int as exploration,
    (domain_scores->>'verbal')::int as verbal,
    GREATEST(
        (domain_scores->>'sensation')::int,
        (domain_scores->>'connection')::int,
        (domain_scores->>'power')::int,
        (domain_scores->>'exploration')::int,
        (domain_scores->>'verbal')::int
    ) as max_domain_score,
    LEAST(
        (domain_scores->>'sensation')::int,
        (domain_scores->>'connection')::int,
        (domain_scores->>'power')::int,
        (domain_scores->>'exploration')::int,
        (domain_scores->>'verbal')::int
    ) as min_domain_score
FROM profiles
WHERE domain_scores IS NOT NULL AND user_id IS NOT NULL
ORDER BY user_id;

-- Optional: Get raw distribution for a specific domain (e.g., Sensation)
-- Uncomment to use
/*
SELECT 
    (domain_scores->>'sensation')::int as score, 
    COUNT(*) as frequency 
FROM profiles 
WHERE domain_scores IS NOT NULL 
GROUP BY 1 
ORDER BY 1;
*/
