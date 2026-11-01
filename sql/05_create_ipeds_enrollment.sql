-- EdAtlas: IPEDS Fall Enrollment 2024
-- One record per institution (UNITID).

CREATE TABLE IF NOT EXISTS public.ipeds_enrollment_2024 (
    school_id BIGINT PRIMARY KEY,
    total_enrollment BIGINT NOT NULL
        CHECK (total_enrollment >= 0),
    male_enrollment BIGINT NOT NULL
        CHECK (male_enrollment >= 0),
    female_enrollment BIGINT NOT NULL
        CHECK (female_enrollment >= 0),
    reporting_flag VARCHAR(5),
    CONSTRAINT valid_enrollment_totals
        CHECK (
            male_enrollment + female_enrollment
            = total_enrollment
        )
);
