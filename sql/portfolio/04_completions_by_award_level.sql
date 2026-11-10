
-- Purpose: Analyze the distribution of 2024 program completions.
-- Grain: One row per award level.
-- Note: Counts represent awards, not necessarily unique students.

WITH award_totals AS (
    SELECT
        c.award_level,
        COUNT(DISTINCT c.school_id) AS reporting_institutions,
        SUM(c.total_awards) AS total_awards,
        SUM(c.male_awards) AS male_awards,
        SUM(c.female_awards) AS female_awards
    FROM dw.fact_completions c
    WHERE c.award_year = 2024
    GROUP BY c.award_level
)
SELECT
    a.award_level,
    a.reporting_institutions,
    a.total_awards,
    a.male_awards,
    a.female_awards,
    RANK() OVER (
        ORDER BY a.total_awards DESC
    ) AS awards_rank,
    ROUND(
        100.0 * a.total_awards
        / NULLIF(SUM(a.total_awards) OVER (), 0),
        2
    ) AS share_of_awards_pct
FROM award_totals a
ORDER BY awards_rank, award_level;
