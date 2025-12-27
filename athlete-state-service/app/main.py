"""
AthleteState Service - FastAPI application
"""
from fastapi import FastAPI, HTTPException, status, Body
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os
from typing import Dict, Any, Optional
from datetime import date, datetime
import json

# Fix Python path
sys.path.insert(0, '/app')

# Now import - NO DOT before models!
from models import AthleteState
from managers import AthleteStateManager

# Initialize manager
manager = AthleteStateManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    print("🚀 Starting AthleteState Service")
    await manager.initialize()
    yield
    print("🛑 Shutting down")
    await manager.cleanup()

app = FastAPI(
    title="AthleteState Service",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"service": "AthleteState", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/state/{athlete_id}")
async def get_state(athlete_id: int):
    try:
        state = await manager.get_state(athlete_id)
        if state:
            return {"success": True, "state": state.to_dict()}
        else:
            raise HTTPException(404, f"Athlete {athlete_id} not found")
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@app.patch("/api/v1/state/{athlete_id}")
async def update_athlete_state(
    athlete_id: int,
    updates: Dict[str, Any] = Body(...)
):
    """Update athlete state with partial updates"""
    try:
        success = await manager.update_state(athlete_id, updates)
        if success:
            # Get updated state to return
            state = await manager.get_state(athlete_id)
            return {
                "success": True,
                "athlete_id": athlete_id,
                "state": state.to_dict() if state else None,
                "message": "State updated successfully"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to update athlete {athlete_id}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )

@app.post("/api/v1/events")
async def log_coaching_event(
    athlete_id: int = Body(...),
    event_type: str = Body(...),
    trigger: Optional[str] = Body(None),
    decision: Optional[str] = Body(None),
    rationale: Optional[str] = Body(None),
    metadata: Optional[Dict[str, Any]] = Body(None)
):
    """Log a coaching event"""
    try:
        await manager.log_coaching_event(
            athlete_id=athlete_id,
            event_type=event_type,
            trigger=trigger,
            decision=decision,
            rationale=rationale,
            metadata=metadata
        )
        return {
            "success": True,
            "message": f"Event logged for athlete {athlete_id}",
            "event_type": event_type
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )

# ========== CALENDAR ENDPOINTS ==========

@app.get("/api/v1/calendar/{athlete_id}/{year}/{month}")
async def get_calendar_month(athlete_id: int, year: int, month: int):
    """Get calendar data for a specific month"""
    try:
        # Use the calendar_view we created
        async with manager.pg_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM calendar_view 
                WHERE athlete_id = $1 
                AND EXTRACT(YEAR FROM scheduled_date) = $2
                AND EXTRACT(MONTH FROM scheduled_date) = $3
                ORDER BY scheduled_date
            """, athlete_id, year, month)
            
            days = []
            for row in rows:
                day_data = dict(row)
                # Convert date to string for JSON
                if day_data.get('scheduled_date'):
                    day_data['scheduled_date'] = day_data['scheduled_date'].isoformat()
                days.append(day_data)
            
            return {
                "success": True,
                "athlete_id": athlete_id,
                "month": f"{year}-{month:02d}",
                "days": days
            }
            
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@app.get("/api/v1/calendar/{athlete_id}/workout/{workout_id}")
async def get_workout_details(athlete_id: int, workout_id: int):
    """Get detailed workout information"""
    try:
        async with manager.pg_pool.acquire() as conn:
            workout = await conn.fetchrow("""
                SELECT * FROM planned_workouts 
                WHERE id = $1 AND athlete_id = $2
            """, workout_id, athlete_id)
            
            if not workout:
                raise HTTPException(404, "Workout not found")
            
            # Get coaching events for this workout
            events = await conn.fetch("""
                SELECT event_type, trigger, decision, rationale, created_at
                FROM coaching_events 
                WHERE athlete_id = $1 
                AND metadata->>'workout_id' = $2
                ORDER BY created_at DESC
                LIMIT 5
            """, athlete_id, str(workout_id))
            
            workout_dict = dict(workout)
            # Convert date and timestamps to strings
            if workout_dict.get('scheduled_date'):
                workout_dict['scheduled_date'] = workout_dict['scheduled_date'].isoformat()
            if workout_dict.get('created_at'):
                workout_dict['created_at'] = workout_dict['created_at'].isoformat()
            
            return {
                "success": True,
                "workout": workout_dict,
                "coaching_events": [dict(e) for e in events]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@app.patch("/api/v1/calendar/{athlete_id}/workout/{workout_id}")
async def update_workout(
    athlete_id: int,
    workout_id: int,
    updates: Dict[str, Any] = Body(...)
):
    """Update workout (environment, status, feedback, etc.)"""
    try:
        allowed_updates = {
            'environment', 'completion_status', 'actual_tss',
            'athlete_feedback_rpe', 'athlete_feedback_notes',
            'strava_activity_id'
        }
        
        # Filter allowed updates
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_updates}
        
        if not filtered_updates:
            raise HTTPException(400, "No valid fields to update")
        
        async with manager.pg_pool.acquire() as conn:
            # Build update query
            set_clauses = []
            params = []
            param_index = 1
            
            for field, value in filtered_updates.items():
                set_clauses.append(f"{field} = ${param_index}")
                params.append(value)
                param_index += 1
            
            params.extend([workout_id, athlete_id])
            
            query = f"""
                UPDATE planned_workouts 
                SET {', '.join(set_clauses)}
                WHERE id = ${param_index} AND athlete_id = ${param_index + 1}
                RETURNING *
            """
            
            updated = await conn.fetchrow(query, *params)
            
            if not updated:
                raise HTTPException(404, "Workout not found")
            
            # Log coaching event if status changed
            if 'completion_status' in filtered_updates:
                await manager.log_coaching_event(
                    athlete_id=athlete_id,
                    event_type="workout_status_updated",
                    trigger="athlete_update",
                    decision=f"Set status to {filtered_updates['completion_status']}",
                    rationale="Athlete updated workout status",
                    metadata={"workout_id": workout_id, **filtered_updates}
                )
            
            return {
                "success": True,
                "message": "Workout updated",
                "workout": dict(updated)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

# Simple .ZWO file generator (no httpx dependency)
def generate_zwo_file(workout: dict) -> str:
    """Generate .ZWO file content for Zwift"""
    workout_type = workout.get('workout_type', 'endurance')
    duration = workout.get('duration_minutes', 60)
    
    # Simple template based on workout type
    if workout_type == 'threshold':
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<workout>
    <name>Threshold Intervals</name>
    <description>{workout.get('description', 'Threshold workout')}</description>
    <sportType>bike</sportType>
    <author>AI Cycling Coach</author>
    <workout>
        <Warmup Duration="600" PowerLow="0.50" PowerHigh="0.65"/>
        <SteadyState Duration="900" Power="0.95"/>
        <FreeRide Duration="300"/>
        <SteadyState Duration="900" Power="0.95"/>
        <FreeRide Duration="300"/>
        <SteadyState Duration="900" Power="0.95"/>
        <Cooldown Duration="300" PowerLow="0.50" PowerHigh="0.50"/>
    </workout>
</workout>"""
    elif workout_type == 'endurance':
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<workout>
    <name>Endurance Ride</name>
    <description>{workout.get('description', 'Endurance workout')}</description>
    <sportType>bike</sportType>
    <author>AI Cycling Coach</author>
    <workout>
        <Warmup Duration="600" PowerLow="0.50" PowerHigh="0.65"/>
        <SteadyState Duration="{max(300, duration * 60 - 1200)}" Power="0.70"/>
        <Cooldown Duration="300" PowerLow="0.50" PowerHigh="0.50"/>
    </workout>
</workout>"""
    else:
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<workout>
    <name>{workout_type.title()} Workout</name>
    <description>{workout.get('description', '')}</description>
    <sportType>bike</sportType>
    <author>AI Cycling Coach</author>
    <workout>
        <Warmup Duration="600" PowerLow="0.50" PowerHigh="0.65"/>
        <SteadyState Duration="{max(300, duration * 60 - 1200)}" Power="0.75"/>
        <Cooldown Duration="300" PowerLow="0.50" PowerHigh="0.50"/>
    </workout>
</workout>"""

@app.get("/api/v1/calendar/{athlete_id}/workout/{workout_id}/file/{file_type}")
async def download_workout_file(
    athlete_id: int,
    workout_id: int,
    file_type: str
):
    """Download workout file (.fit or .zwo) - SIMPLIFIED"""
    if file_type not in ['fit', 'zwo']:
        raise HTTPException(400, "File type must be 'fit' or 'zwo'")
    
    try:
        async with manager.pg_pool.acquire() as conn:
            # Get workout details
            workout = await conn.fetchrow("""
                SELECT * FROM planned_workouts 
                WHERE id = $1 AND athlete_id = $2
            """, workout_id, athlete_id)
            
            if not workout:
                raise HTTPException(404, "Workout not found")
            
            workout_dict = dict(workout)
            
            if file_type == 'fit':
                # Placeholder for .FIT file
                content = b"FIT_FILE_PLACEHOLDER - Connect to .FIT service later"
                
                # Update database
                await conn.execute("""
                    UPDATE planned_workouts 
                    SET fit_file_generated = TRUE 
                    WHERE id = $1
                """, workout_id)
                
                from fastapi import Response
                return Response(
                    content=content,
                    media_type="application/octet-stream",
                    headers={
                        "Content-Disposition": f"attachment; filename=workout_{workout_id}.fit"
                    }
                )
            
            elif file_type == 'zwo':
                # Generate .ZWO file
                zwo_content = generate_zwo_file(workout_dict)
                
                # Update database
                await conn.execute("""
                    UPDATE planned_workouts 
                    SET zwo_file_generated = TRUE 
                    WHERE id = $1
                """, workout_id)
                
                from fastapi import Response
                return Response(
                    content=zwo_content.encode('utf-8'),
                    media_type="application/xml",
                    headers={
                        "Content-Disposition": f"attachment; filename=workout_{workout_id}.zwo"
                    }
                )
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
