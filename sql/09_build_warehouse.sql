-- EdAtlas warehouse: full rebuild of the dw schema from the public source tables.
-- Safe to re-run. It only drops and recreates schema dw.

DROP SCHEMA IF EXISTS dw CASCADE;
CREATE SCHEMA dw;

-- ---------- Dimensions ----------

CREATE TABLE dw.dim_state (
    state_code   VARCHAR(2) PRIMARY KEY,
    state_name   TEXT NOT NULL,
    has_bls_data BOOLEAN NOT NULL
);

CREATE TABLE dw.dim_institution (
    school_id         BIGINT PRIMARY KEY,
    institution_name  TEXT NOT NULL,
    scorecard_name    TEXT,
    city              TEXT,
    state_code        VARCHAR(2) NOT NULL REFERENCES dw.dim_state (state_code),
    scorecard_state   VARCHAR(2),
    zip_code          TEXT,
    sector            SMALLINT,
    institution_level SMALLINT,
    ownership         SMALLINT,
    hbcu_status       SMALLINT,
    locale            SMALLINT,
    size_category     SMALLINT,
    latitude          DOUBLE PRECISION,
    longitude         DOUBLE PRECISION,
    in_ipeds          BOOLEAN NOT NULL,
    in_scorecard      BOOLEAN NOT NULL
);
CREATE INDEX ix_dim_institution_state ON dw.dim_institution (state_code);

CREATE TABLE dw.dim_occupation (
    occupation_code  VARCHAR(7) PRIMARY KEY
        CHECK (occupation_code ~ '^[0-9]{2}-[0-9]{4}$'),
    occupation_title TEXT NOT NULL
);

CREATE TABLE dw.dim_cip (
    cip_code   VARCHAR(7) PRIMARY KEY
        CHECK (cip_code ~ '^[0-9]{2}\.[0-9]{4}$'),
    cip_family VARCHAR(2) GENERATED ALWAYS AS (left(cip_code, 2)) STORED,
    cip_title  TEXT
);

CREATE TABLE dw.dim_award_level (
    award_level SMALLINT PRIMARY KEY,
    label       TEXT
);

-- ---------- Facts ----------

CREATE TABLE dw.fact_institution_outcomes (
    school_id            BIGINT PRIMARY KEY REFERENCES dw.dim_institution (school_id),
    student_size         BIGINT,
    admission_rate       DOUBLE PRECISION,
    avg_net_price        DOUBLE PRECISION,
    completion_rate      DOUBLE PRECISION,
    median_earnings_10yr DOUBLE PRECISION,
    loaded_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE dw.fact_enrollment (
    school_id         BIGINT NOT NULL REFERENCES dw.dim_institution (school_id),
    enrollment_year   SMALLINT NOT NULL,
    total_enrollment  BIGINT NOT NULL CHECK (total_enrollment >= 0),
    male_enrollment   BIGINT NOT NULL CHECK (male_enrollment >= 0),
    female_enrollment BIGINT NOT NULL CHECK (female_enrollment >= 0),
    reporting_flag    VARCHAR(5),
    PRIMARY KEY (school_id, enrollment_year),
    CHECK (male_enrollment + female_enrollment = total_enrollment)
);

CREATE TABLE dw.fact_completions (
    school_id      BIGINT NOT NULL REFERENCES dw.dim_institution (school_id),
    award_year     SMALLINT NOT NULL,
    cip_code       VARCHAR(7) NOT NULL REFERENCES dw.dim_cip (cip_code),
    award_level    SMALLINT NOT NULL REFERENCES dw.dim_award_level (award_level),
    total_awards   BIGINT NOT NULL CHECK (total_awards >= 0),
    male_awards    BIGINT NOT NULL CHECK (male_awards >= 0),
    female_awards  BIGINT NOT NULL CHECK (female_awards >= 0),
    reporting_flag VARCHAR(5),
    PRIMARY KEY (school_id, award_year, cip_code, award_level),
    CHECK (male_awards + female_awards = total_awards)
);
CREATE INDEX ix_fact_completions_cip ON dw.fact_completions (cip_code);

CREATE TABLE dw.fact_occupation_wages (
    reference_year          SMALLINT NOT NULL,
    state_code              VARCHAR(2) NOT NULL REFERENCES dw.dim_state (state_code),
    occupation_code         VARCHAR(7) NOT NULL REFERENCES dw.dim_occupation (occupation_code),
    area_type               SMALLINT NOT NULL,
    employment              BIGINT CHECK (employment >= 0),
    employment_flag         VARCHAR(5),
    annual_mean_wage        NUMERIC(12, 2) CHECK (annual_mean_wage >= 0),
    annual_mean_wage_flag   VARCHAR(5),
    annual_median_wage      NUMERIC(12, 2) CHECK (annual_median_wage >= 0),
    annual_median_wage_flag VARCHAR(5),
    hourly_mean_wage        NUMERIC(10, 2) CHECK (hourly_mean_wage >= 0),
    hourly_mean_wage_flag   VARCHAR(5),
    hourly_median_wage      NUMERIC(10, 2) CHECK (hourly_median_wage >= 0),
    hourly_median_wage_flag VARCHAR(5),
    PRIMARY KEY (reference_year, state_code, occupation_code)
);
CREATE INDEX ix_fact_wages_occupation ON dw.fact_occupation_wages (occupation_code);

-- ---------- Load dimensions ----------

INSERT INTO dw.dim_state (state_code, state_name, has_bls_data)
SELECT DISTINCT state, state_name, TRUE FROM public.bls_oews_state_2025;

INSERT INTO dw.dim_state (state_code, state_name, has_bls_data) VALUES
    ('AS', 'American Samoa', FALSE),
    ('FM', 'Federated States of Micronesia', FALSE),
    ('MH', 'Marshall Islands', FALSE),
    ('MP', 'Northern Mariana Islands', FALSE),
    ('PW', 'Palau', FALSE);

INSERT INTO dw.dim_institution (
    school_id, institution_name, scorecard_name, city, state_code,
    scorecard_state, zip_code, sector, institution_level, ownership,
    hbcu_status, locale, size_category, latitude, longitude,
    in_ipeds, in_scorecard)
SELECT
    COALESCE(ip.school_id, cs.school_id),
    COALESCE(ip.institution_name, cs.school_name),
    cs.school_name,
    COALESCE(ip.city, cs.city),
    COALESCE(ip.state, cs.state),
    cs.state,
    cs.zip_code,
    ip.sector,
    ip.institution_level,
    COALESCE(ip.ownership, cs.ownership::int),
    ip.hbcu_status,
    COALESCE(ip.locale, ROUND(cs.locale)::int),
    ip.institution_size_category,
    COALESCE(ip.latitude, cs.latitude),
    COALESCE(ip.longitude, cs.longitude),
    ip.school_id IS NOT NULL,
    cs.school_id IS NOT NULL
FROM public.ipeds_institutions ip
FULL OUTER JOIN public.college_scorecard cs ON ip.school_id = cs.school_id;

INSERT INTO dw.dim_occupation (occupation_code, occupation_title)
SELECT DISTINCT occupation_code, occupation_title FROM public.bls_oews_state_2025;

INSERT INTO dw.dim_cip (cip_code)
SELECT DISTINCT cip_code FROM public.ipeds_completions_programs_2024;

INSERT INTO dw.dim_award_level (award_level)
SELECT award_level FROM public.ipeds_completions_programs_2024
UNION
SELECT award_level FROM public.ipeds_completions_totals_2024;

-- ---------- Load facts ----------

INSERT INTO dw.fact_institution_outcomes (
    school_id, student_size, admission_rate, avg_net_price,
    completion_rate, median_earnings_10yr)
SELECT school_id, student_size, admission_rate, avg_net_price,
       completion_rate, median_earnings_10yr
FROM public.college_scorecard;

INSERT INTO dw.fact_enrollment (
    school_id, enrollment_year, total_enrollment, male_enrollment,
    female_enrollment, reporting_flag)
SELECT school_id, 2024, total_enrollment, male_enrollment,
       female_enrollment, reporting_flag
FROM public.ipeds_enrollment_2024;

INSERT INTO dw.fact_completions (
    school_id, award_year, cip_code, award_level, total_awards,
    male_awards, female_awards, reporting_flag)
SELECT school_id, 2024, cip_code, award_level, total_awards,
       male_awards, female_awards, reporting_flag
FROM public.ipeds_completions_programs_2024;

INSERT INTO dw.fact_occupation_wages (
    reference_year, state_code, occupation_code, area_type,
    employment, employment_flag,
    annual_mean_wage, annual_mean_wage_flag,
    annual_median_wage, annual_median_wage_flag,
    hourly_mean_wage, hourly_mean_wage_flag,
    hourly_median_wage, hourly_median_wage_flag)
SELECT reference_year, state, occupation_code, area_type,
       employment, employment_flag,
       annual_mean_wage, annual_mean_wage_flag,
       annual_median_wage, annual_median_wage_flag,
       hourly_mean_wage, hourly_mean_wage_flag,
       hourly_median_wage, hourly_median_wage_flag
FROM public.bls_oews_state_2025;

-- ---------- Convenience view ----------

CREATE VIEW dw.vw_institution_overview AS
SELECT
    i.school_id,
    i.institution_name,
    i.city,
    i.state_code,
    s.state_name,
    i.ownership,
    i.in_ipeds,
    i.in_scorecard,
    e.total_enrollment,
    o.admission_rate,
    ROUND((o.admission_rate * 100)::numeric, 2)  AS admission_rate_pct,
    o.completion_rate,
    ROUND((o.completion_rate * 100)::numeric, 2) AS completion_rate_pct,
    o.avg_net_price,
    o.median_earnings_10yr
FROM dw.dim_institution i
JOIN dw.dim_state s ON s.state_code = i.state_code
LEFT JOIN dw.fact_enrollment e
       ON e.school_id = i.school_id AND e.enrollment_year = 2024
LEFT JOIN dw.fact_institution_outcomes o ON o.school_id = i.school_id;

ANALYZE;
