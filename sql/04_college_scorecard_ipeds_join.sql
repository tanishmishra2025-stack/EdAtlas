
-- EdAtlas: College Scorecard + IPEDS 2024
-- Join institutions using their shared school_id.

SELECT
    cs.school_id,
    cs.school_name,
    cs.state,
    cs.student_size,
    cs.admission_rate,
    cs.avg_net_price,
    cs.completion_rate,
    cs.median_earnings_10yr,
    ip.institution_level,
    ip.sector,
    ip.institution_size_category,
    ip.hbcu_status
FROM college_scorecard AS cs
INNER JOIN ipeds_institutions AS ip
    ON cs.school_id = ip.school_id
ORDER BY cs.school_name;
