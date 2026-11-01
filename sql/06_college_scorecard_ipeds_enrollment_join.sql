
-- EdAtlas: College Scorecard + IPEDS + Fall Enrollment 2024
-- One row per institution present in all three datasets.

SELECT
    cs.school_id,
    cs.school_name,
    cs.state,
    cs.student_size AS scorecard_student_size,
    e.total_enrollment AS ipeds_total_enrollment,
    e.male_enrollment,
    e.female_enrollment,
    e.reporting_flag,
    cs.admission_rate,
    cs.avg_net_price,
    cs.completion_rate,
    cs.median_earnings_10yr,
    ip.sector,
    ip.institution_level,
    ip.institution_size_category
FROM public.college_scorecard AS cs
INNER JOIN public.ipeds_institutions AS ip
    ON cs.school_id = ip.school_id
INNER JOIN public.ipeds_enrollment_2024 AS e
    ON ip.school_id = e.school_id
ORDER BY cs.school_id;
