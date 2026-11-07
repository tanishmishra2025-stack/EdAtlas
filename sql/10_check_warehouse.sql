-- Every row should show ok = t.
SELECT check_name, actual, expected, (actual = expected) AS ok
FROM (
    SELECT 'dim_institution rows' AS check_name,
           (SELECT COUNT(*) FROM dw.dim_institution)::numeric AS actual,
           6615::numeric AS expected
    UNION ALL SELECT 'institutions in both sources',
           (SELECT COUNT(*) FROM dw.dim_institution WHERE in_ipeds AND in_scorecard), 5730
    UNION ALL SELECT 'dim_state rows', (SELECT COUNT(*) FROM dw.dim_state), 59
    UNION ALL SELECT 'dim_occupation rows', (SELECT COUNT(*) FROM dw.dim_occupation), 829
    UNION ALL SELECT 'dim_cip rows', (SELECT COUNT(*) FROM dw.dim_cip), 1607
    UNION ALL SELECT 'fact_institution_outcomes rows',
           (SELECT COUNT(*) FROM dw.fact_institution_outcomes), 6273
    UNION ALL SELECT 'fact_enrollment rows', (SELECT COUNT(*) FROM dw.fact_enrollment), 5842
    UNION ALL SELECT 'fact_completions rows', (SELECT COUNT(*) FROM dw.fact_completions), 267595
    UNION ALL SELECT 'fact_occupation_wages rows',
           (SELECT COUNT(*) FROM dw.fact_occupation_wages), 36168
    UNION ALL SELECT 'awards total matches source',
           (SELECT SUM(total_awards) FROM dw.fact_completions),
           (SELECT SUM(total_awards) FROM public.ipeds_completions_programs_2024)
    UNION ALL SELECT 'enrollment total matches source',
           (SELECT SUM(total_enrollment) FROM dw.fact_enrollment),
           (SELECT SUM(total_enrollment) FROM public.ipeds_enrollment_2024)
    UNION ALL SELECT 'employment total matches source',
           (SELECT SUM(employment) FROM dw.fact_occupation_wages),
           (SELECT SUM(employment) FROM public.bls_oews_state_2025)
    UNION ALL SELECT 'program awards vs institution totals (mismatches)',
           (SELECT COUNT(*) FROM public.ipeds_completions_totals_2024 t
            LEFT JOIN (SELECT school_id, award_level, SUM(total_awards) AS s
                       FROM dw.fact_completions GROUP BY 1, 2) p
                   ON p.school_id = t.school_id AND p.award_level = t.award_level
            WHERE COALESCE(p.s, 0) <> t.total_awards), 0
) t
ORDER BY ok, check_name;

-- Informational: matched institutions that disagree on state
SELECT school_id, institution_name, scorecard_name, state_code, scorecard_state
FROM dw.dim_institution
WHERE in_ipeds AND in_scorecard AND state_code <> scorecard_state;

-- Informational: ownership and locale disagreements between the sources
SELECT
    COUNT(*) FILTER (WHERE ip.ownership <> cs.ownership) AS ownership_disagreements,
    COUNT(*) FILTER (WHERE ip.locale <> ROUND(cs.locale)::int) AS locale_disagreements
FROM public.ipeds_institutions ip
JOIN public.college_scorecard cs ON cs.school_id = ip.school_id;
