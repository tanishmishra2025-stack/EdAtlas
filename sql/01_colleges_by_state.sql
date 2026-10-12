SELECT
    state,
    COUNT(*) AS total_colleges
FROM college_scorecard
GROUP BY state
ORDER BY total_colleges DESC
LIMIT 10;