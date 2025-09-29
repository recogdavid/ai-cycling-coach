#!/bin/bash
set -e

# This script is executed by the PostgreSQL entrypoint
# in the /docker-entrypoint-initdb.d/ directory.
# It ensures all required application tables and indices are created.

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL

    -- =================================================================
    -- Table 1: CyclistProfile (Central athlete profile)
    -- PK is strava_athlete_id for easy lookups
    -- =================================================================
    CREATE TABLE IF NOT EXISTS CyclistProfile (
        strava_athlete_id BIGINT PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        height_cm INTEGER,
        weight_kg NUMERIC(5, 2),
        ftp INTEGER,
        current_fitness_level VARCHAR(50),
        primary_goal TEXT,
        goal_event_date DATE,
        time_available_weekly INTEGER,
        primary_training_env VARCHAR(50),
        indoor_platform VARCHAR(50),
        prefers_indoor BOOLEAN DEFAULT FALSE,
        indoor_season_months VARCHAR(255),
        preferred_zone_system VARCHAR(50),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- =================================================================
    -- Table 2: TrainingZones (User-specific zone definitions)
    -- =================================================================
    CREATE TABLE IF NOT EXISTS TrainingZones (
        id BIGSERIAL PRIMARY KEY,
        strava_athlete_id BIGINT NOT NULL REFERENCES CyclistProfile(strava_athlete_id),
        zone_system VARCHAR(50) NOT NULL,
        zones_json JSONB NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- =================================================================
    -- Table 3: WorkoutMetrics (Planned vs. Actual activity data)
    -- =================================================================
    CREATE TABLE IF NOT EXISTS WorkoutMetrics (
        id BIGSERIAL PRIMARY KEY,
        strava_athlete_id BIGINT NOT NULL REFERENCES CyclistProfile(strava_athlete_id),
        strava_activity_id BIGINT NOT NULL UNIQUE,
        workout_type VARCHAR(50),
        planned_tss INTEGER,
        planned_duration INTEGER,
        planned_intensity_factor NUMERIC(4, 2),
        planned_normalized_power INTEGER,
        planned_workout_structure JSONB,
        actual_tss INTEGER,
        actual_duration INTEGER,
        actual_intensity_factor NUMERIC(4, 2),
        actual_normalized_power INTEGER,
        actual_avg_power INTEGER,
        actual_avg_heartrate INTEGER,
        actual_watts_per_kg NUMERIC(4, 2),
        tss_difference INTEGER,
        intensity_comparison VARCHAR(50),
        adherence_score NUMERIC(5, 2),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- =================================================================
    -- Table 4: WeeklyTrainingLoad (ATL/CTL/TSB Tracking)
    -- =================================================================
    CREATE TABLE IF NOT EXISTS WeeklyTrainingLoad (
        id BIGSERIAL PRIMARY KEY,
        strava_athlete_id BIGINT NOT NULL REFERENCES CyclistProfile(strava_athlete_id),
        week_start_date DATE NOT NULL,
        planned_tss INTEGER,
        actual_tss INTEGER,
        tss_balance INTEGER,
        acute_training_load NUMERIC(6, 2),
        chronic_training_load NUMERIC(6, 2),
        training_stress_balance NUMERIC(6, 2),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (strava_athlete_id, week_start_date)
    );

    -- =================================================================
    -- Indexing for performance
    -- =================================================================
    CREATE INDEX IF NOT EXISTS idx_metrics_athlete_id ON WorkoutMetrics (strava_athlete_id);
    CREATE INDEX IF NOT EXISTS idx_load_athlete_week ON WeeklyTrainingLoad (strava_athlete_id, week_start_date);

EOSQL
