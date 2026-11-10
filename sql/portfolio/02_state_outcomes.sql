SELECT i.state_code, COUNT(*) AS institutions_in_scorecard,
COUNT(o.avg_net_price) FILTER (WHERE o.avg_net_price >= 0) AS institutions_with_price,
ROUND(AVG(o.avg_net_price) FILTER (WHERE o.avg_net_price >= 0)::numeric, 2) AS avg_net_price,
COUNT(o.completion_rate) FILTER (WHERE o.completion_rate BETWEEN 0 AND 1) AS institutions_with_completion,
ROUND((AVG(o.completion_rate) FILTER (WHERE o.completion_rate BETWEEN 0 AND 1) * 100)::numeric, 2) AS avg_completion_pct
FROM dw.dim_institution i
JOIN dw.fact_institution_outcomes o ON i.school_id = o.school_id
GROUP BY i.state_code
ORDER BY institutions_in_scorecard DESC, i.state_code
LIMIT 10;
