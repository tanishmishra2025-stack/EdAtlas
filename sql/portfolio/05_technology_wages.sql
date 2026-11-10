
-- Purpose: Compare reported technology occupation wages across states.
-- Source: BLS OEWS 2025.
-- Grain: One row per state and occupation.
-- Caveat: Wages are not adjusted for cost of living.
-- Missing or suppressed median wages are excluded from rankings.

WITH technology_wages AS (
    SELECT
        s.state_name,
        w.state_code,
        w.occupation_code,
        o.occupation_title,
        w.reference_year,
        w.employment,
        w.annual_mean_wage,
        w.annual_median_wage,
        w.annual_median_wage_flag
    FROM dw.fact_occupation_wages w
    JOIN dw.dim_state s
        ON w.state_code = s.state_code
    JOIN dw.dim_occupation o
        ON w.occupation_code = o.occupation_code
    WHERE w.reference_year = 2025
      AND w.occupation_code IN (
          '15-1252',  -- Software Developers
          '15-2051',  -- Data Scientists
          '15-1242'   -- Database Administrators
      )
),
ranked_wages AS (
    SELECT
        *,
        RANK() OVER (
            PARTITION BY occupation_code
            ORDER BY annual_median_wage DESC NULLS LAST
        ) AS wage_rank
    FROM technology_wages
    WHERE annual_median_wage IS NOT NULL
)
SELECT
    occupation_code,
    occupation_title,
    wage_rank,
    state_name,
    employment,
    annual_mean_wage,
    annual_median_wage,
    annual_median_wage_flag
FROM ranked_wages
WHERE wage_rank <= 5
ORDER BY occupation_code, wage_rank, state_name;
