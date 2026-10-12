SELECT
    school_name,
    state,
    ROUND(avg_net_price::numeric, 2) AS net_price,
    ROUND(median_earnings_10yr::numeric, 2) AS median_earnings,
    ROUND(
        (median_earnings_10yr / NULLIF(avg_net_price, 0))::numeric,
        2
    ) AS earnings_to_price_ratio
FROM college_scorecard
WHERE avg_net_price >= 5000
  AND median_earnings_10yr > 0
ORDER BY earnings_to_price_ratio DESC
LIMIT 10;