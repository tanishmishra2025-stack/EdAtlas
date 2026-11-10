
-- Purpose: Compare reported 2024 enrollment across states.
-- Grain: One row per state.
-- National share is calculated before selecting the top 10 states.

WITH state_enrollment AS (
    SELECT
        s.state_code,
        s.state_name,
        COUNT(*) AS reporting_institutions,
        SUM(e.total_enrollment) AS total_enrollment,
        SUM(e.male_enrollment) AS male_enrollment,
        SUM(e.female_enrollment) AS female_enrollment
    FROM dw.fact_enrollment e
    JOIN dw.dim_institution i
        ON e.school_id = i.school_id
    JOIN dw.dim_state s
        ON i.state_code = s.state_code
    WHERE e.enrollment_year = 2024
    GROUP BY s.state_code, s.state_name
),
ranked_states AS (
    SELECT
        *,
        RANK() OVER (
            ORDER BY total_enrollment DESC
        ) AS enrollment_rank,
        ROUND(
            100.0 * total_enrollment
            / NULLIF(SUM(total_enrollment) OVER (), 0),
            2
        ) AS national_enrollment_pct
    FROM state_enrollment
)
SELECT
    enrollment_rank,
    state_name,
    reporting_institutions,
    total_enrollment,
    male_enrollment,
    female_enrollment,
    national_enrollment_pct
FROM ranked_states
ORDER BY enrollment_rank, state_name
LIMIT 10;
