
-- EdAtlas: BLS OEWS May 2025
-- Detailed occupational employment and wages by geographic area.

CREATE TABLE IF NOT EXISTS public.bls_oews_state_2025 (
    reference_year INTEGER NOT NULL,
    state VARCHAR(2) NOT NULL,
    state_name TEXT NOT NULL,
    area_type INTEGER NOT NULL,
    occupation_code VARCHAR(10) NOT NULL,
    occupation_title TEXT NOT NULL,

    employment BIGINT CHECK (employment >= 0),
    employment_flag VARCHAR(5),

    annual_mean_wage NUMERIC(12, 2)
        CHECK (annual_mean_wage >= 0),
    annual_mean_wage_flag VARCHAR(5),

    annual_median_wage NUMERIC(12, 2)
        CHECK (annual_median_wage >= 0),
    annual_median_wage_flag VARCHAR(5),

    hourly_mean_wage NUMERIC(10, 2)
        CHECK (hourly_mean_wage >= 0),
    hourly_mean_wage_flag VARCHAR(5),

    hourly_median_wage NUMERIC(10, 2)
        CHECK (hourly_median_wage >= 0),
    hourly_median_wage_flag VARCHAR(5),

    PRIMARY KEY (
        reference_year,
        state,
        occupation_code
    )
);
