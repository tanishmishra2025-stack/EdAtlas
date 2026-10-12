SELECT
    state,
    COUNT(avg_net_price) AS colleges_with_price,
    ROUND(AVG(avg_net_price)::numeric, 2) AS average_net_price
FROM college_scorecard
WHERE avg_net_price >= 0
GROUP BY state
HAVING COUNT(avg_net_price) >= 20
ORDER BY average_net_price DESC
LIMIT 10;