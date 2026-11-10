
-- Compare summed program completions with institution totals.
-- Differences require investigation before reporting award totals.

WITH programs AS (
    SELECT
        school_id,
        award_level,
        SUM(total_awards) AS program_awards
    FROM dw.fact_completions
    WHERE award_year = 2024
    GROUP BY school_id, award_level
),
totals AS (
    SELECT
        school_id,
        award_level,
        SUM(total_awards) AS institution_awards
    FROM public.ipeds_completions_totals_2024
    GROUP BY school_id, award_level
)
SELECT
    COUNT(*) AS institution_award_groups,
    COUNT(*) FILTER (
        WHERE p.school_id IS NULL
           OR t.school_id IS NULL
    ) AS unmatched_groups,
    COUNT(*) FILTER (
        WHERE p.program_awards = t.institution_awards
    ) AS matching_groups,
    COUNT(*) FILTER (
        WHERE p.program_awards <> t.institution_awards
    ) AS mismatching_groups,
    SUM(p.program_awards) AS summed_program_awards,
    SUM(t.institution_awards) AS summed_institution_awards
FROM programs p
FULL OUTER JOIN totals t
    ON p.school_id = t.school_id
   AND p.award_level = t.award_level;
