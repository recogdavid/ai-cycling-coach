"""
Simple initial migration - copies basic athlete data to new tables
"""
import psycopg2
import json
from datetime import datetime
import sys

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host="postgres",  # Docker service name
        database="aicoach_db",
        user="aicoach_user",
        password="D4bosch!609",
        port=5432
    )

def migrate_athletes():
    """Migrate basic athlete data to athlete_state table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("Starting athlete migration...")
    
    try:
        # Get all athletes
        cursor.execute("SELECT id, weekly_hours_available, unavailable_days, environment_preference, strava_ftp FROM athletes")
        athletes = cursor.fetchall()
        
        migrated_count = 0
        for athlete in athletes:
            athlete_id, weekly_hours, unavailable_days, env_pref, ftp = athlete
            
            # Build time availability profile
            time_profile = {
                "weekly_hours_available": weekly_hours or 0,
                "unavailable_days": unavailable_days or [],
                "environment_preference": env_pref or "mixed"
            }
            
            # Insert into athlete_state
            cursor.execute("""
                INSERT INTO athlete_state 
                (athlete_id, time_availability_profile, current_ftp, created_at, updated_at)
                VALUES (%s, %s, %s, NOW(), NOW())
                ON CONFLICT (athlete_id) DO UPDATE SET
                time_availability_profile = EXCLUDED.time_availability_profile,
                current_ftp = EXCLUDED.current_ftp,
                updated_at = NOW()
            """, (athlete_id, json.dumps(time_profile), ftp))
            
            migrated_count += 1
            
            # Log first few for verification
            if migrated_count <= 3:
                print(f"  Migrated athlete {athlete_id}")
        
        conn.commit()
        print(f"✓ Migrated {migrated_count} athletes to athlete_state table")
        
        # Show migration status
        cursor.execute("SELECT COUNT(*) as total, COUNT(DISTINCT athlete_id) as migrated FROM athlete_state")
        result = cursor.fetchone()
        print(f"  Total in athlete_state: {result[0]}")
        print(f"  Unique athletes: {result[1]}")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Migration failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def create_initial_coaching_events():
    """Create initial coaching events for athletes with training goals"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\nCreating initial coaching events...")
    
    try:
        cursor.execute("""
            INSERT INTO coaching_events (athlete_id, event_type, trigger, decision, rationale, created_at)
            SELECT 
                a.id,
                'initial_assessment',
                'athlete_onboarding',
                'Athlete onboarded with goal: ' || COALESCE(a.training_goal, 'No specific goal'),
                'Initial assessment based on athlete profile and Strava data',
                NOW()
            FROM athletes a
            WHERE a.training_goal IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM coaching_events ce 
                WHERE ce.athlete_id = a.id 
                AND ce.event_type = 'initial_assessment'
            )
        """)
        
        event_count = cursor.rowcount
        conn.commit()
        print(f"✓ Created {event_count} initial coaching events")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Failed to create coaching events: {e}")
    finally:
        cursor.close()
        conn.close()

def main():
    """Main migration function"""
    print("=" * 50)
    print("AthleteState Migration Tool")
    print("=" * 50)
    
    # Run migrations
    migrate_athletes()
    create_initial_coaching_events()
    
    print("\n" + "=" * 50)
    print("Migration completed!")
    print("Check status with: SELECT * FROM athlete_migration_status;")
    print("=" * 50)

if __name__ == "__main__":
    main()
