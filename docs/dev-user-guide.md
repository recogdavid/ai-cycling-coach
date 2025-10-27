
# Dev User Guide

> **Note:** This is an early prototype. Features are limited and require technical knowledge to use.

## Current Capabilities

### 1. Connect Strava Account

**Status:** Working for single user only

Connect your Strava account to enable automatic activity sync:
```
https://your-domain.com/webhook/api/strava/connect?athlete_id=9
```

### 2. Generate Training Plan

Generate a week-long AI-powered training plan:
```bash
curl -X POST https://your-domain.com/webhook/generate-plan \
  -H "Content-Type: application/json" \
  -d '{"athlete_id": 9}'
```

**What it does:**
- Analyzes your FTP, training goals, and weekly availability
- Creates 7 days of structured workouts
- Respects your unavailable days (e.g., no Monday workouts)
- Varies intensity (Endurance, Tempo, Threshold, VO2, Recovery)

**AI generation time:** 60-90 seconds (on 6-core/12GB server)

### 3. View Your Training Plan

Query the database to see your plan:
```sql
SELECT 
  scheduled_date,
  workout_type,
  description,
  duration_minutes,
  target_tss
FROM planned_workouts
WHERE athlete_id = 9
ORDER BY scheduled_date;
```

### 4. View Workout Details

See the interval structure for a specific workout:
```sql
SELECT 
  description,
  intervals
FROM planned_workouts
WHERE id = <workout_id>;
```

The `intervals` column contains JSON with power targets:
```json
[
  {
    "duration_seconds": 600,
    "power_ftp_percent": 0.65,
    "description": "Warmup"
  },
  {
    "duration_seconds": 300,
    "power_ftp_percent": 0.95,
    "description": "Threshold interval"
  }
]
```

## Setting Your Athlete Profile

Update your preferences in the database:
```sql
UPDATE athletes 
SET 
  ftp_watts = 250,
  training_goal = 'Build aerobic base for spring century',
  weekly_hours_available = 8,
  unavailable_days = '["monday", "friday"]'::jsonb
WHERE id = 9;
```

## Understanding Training Zones

Workouts are prescribed as percentages of your FTP:

| Zone | % FTP | Purpose | Example |
|------|-------|---------|---------|
| Recovery | 50-60% | Active recovery | Easy spin |
| Endurance | 65-75% | Aerobic base | Long steady rides |
| Tempo | 75-85% | Sustainable effort | Tempo intervals |
| Threshold | 90-100% | FTP improvement | 2x20min efforts |
| VO2 Max | 105-120% | Max aerobic power | 5x5min hard |

## What's Not Available Yet

- ❌ No web UI - all interactions via API/database
- ❌ No workout file export (.FIT/.ZWO)
- ❌ No execution tracking (doesn't match rides to planned workouts)
- ❌ Plans don't auto-adapt based on compliance
- ❌ Single user only (hardcoded athlete_id = 9)

## Getting Help

- **Bugs:** Open an issue on GitHub
- **Questions:** Use GitHub Discussions
- **Feature ideas:** GitHub Discussions → Ideas category
