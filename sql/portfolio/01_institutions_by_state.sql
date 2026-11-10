SELECT s.state_name, COUNT(*) AS total_institutions,
COUNT(*) FILTER (WHERE i.in_ipeds) AS ipeds_institutions,
COUNT(*) FILTER (WHERE i.in_scorecard) AS scorecard_institutions
FROM dw.dim_institution i
JOIN dw.dim_state s ON i.state_code = s.state_code
GROUP BY s.state_name
ORDER BY total_institutions DESC
LIMIT 10;
