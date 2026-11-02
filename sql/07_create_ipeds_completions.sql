
-- EdAtlas: IPEDS Completions 2024
-- Program-level awards, excluding second majors and CIP 99 totals.

CREATE TABLE IF NOT EXISTS public.ipeds_completions_programs_2024 (
    school_id BIGINT NOT NULL,
    cip_code VARCHAR(10) NOT NULL,
    award_level INTEGER NOT NULL,
    total_awards BIGINT NOT NULL CHECK (total_awards >= 0),
    male_awards BIGINT NOT NULL CHECK (male_awards >= 0),
    female_awards BIGINT NOT NULL CHECK (female_awards >= 0),
    reporting_flag VARCHAR(5),
    PRIMARY KEY (school_id, cip_code, award_level),
    CONSTRAINT program_awards_reconcile
        CHECK (male_awards + female_awards = total_awards)
);

-- Institution totals by award level, from source CIP 99 records.

CREATE TABLE IF NOT EXISTS public.ipeds_completions_totals_2024 (
    school_id BIGINT NOT NULL,
    award_level INTEGER NOT NULL,
    total_awards BIGINT NOT NULL CHECK (total_awards >= 0),
    male_awards BIGINT NOT NULL CHECK (male_awards >= 0),
    female_awards BIGINT NOT NULL CHECK (female_awards >= 0),
    reporting_flag VARCHAR(5),
    PRIMARY KEY (school_id, award_level),
    CONSTRAINT total_awards_reconcile
        CHECK (male_awards + female_awards = total_awards)
);
