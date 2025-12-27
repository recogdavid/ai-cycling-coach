"""
AthleteStateManager - Production version with Redis and PostgreSQL
Updated to match actual database schema
"""
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import redis.asyncio as redis
import asyncpg

from models import AthleteState

class DatabaseConfig:
    """Database configuration"""
    POSTGRES_DSN = "postgresql://aicoach_user:D4bosch!609@postgres:5432/aicoach_db"
    REDIS_URL = "redis://redis:6379"
    REDIS_TTL = 86400  # 24 hours in seconds

class AthleteStateManager:
    """Production manager with Redis cache and PostgreSQL storage"""
    
    def __init__(self):
        self.redis_client = None
        self.pg_pool = None
        self.last_operation_cached = False
        self._fallback_cache = {}  # Fallback in-memory cache
    
    async def initialize(self):
        """Initialize database connections with fallback"""
        print("🔌 Initializing database connections...")
        
        # Initialize Redis
        try:
            self.redis_client = redis.from_url(
                DatabaseConfig.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            await self.redis_client.ping()
            print("✅ Redis connection established")
        except Exception as e:
            print(f"⚠️ Redis connection failed, using fallback: {e}")
            self.redis_client = None
        
        # Initialize PostgreSQL
        try:
            self.pg_pool = await asyncpg.create_pool(
                dsn=DatabaseConfig.POSTGRES_DSN,
                min_size=1,
                max_size=5,
                command_timeout=30,
                server_settings={'search_path': 'public'}
            )
            print("✅ PostgreSQL connection pool established")
        except Exception as e:
            print(f"⚠️ PostgreSQL connection failed, using fallback: {e}")
            self.pg_pool = None
        
        if not self.redis_client and not self.pg_pool:
            print("⚠️ Using in-memory fallback only")
    
    async def cleanup(self):
        """Clean up database connections"""
        print("🧹 Cleaning up database connections...")
        
        if self.redis_client:
            await self.redis_client.close()
            print("✅ Redis connection closed")
        
        if self.pg_pool:
            await self.pg_pool.close()
            print("✅ PostgreSQL connection pool closed")
    
    async def check_database_connection(self) -> bool:
        """Check if PostgreSQL connection is healthy"""
        if not self.pg_pool:
            return False
        try:
            async with self.pg_pool.acquire() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    async def check_redis_connection(self) -> bool:
        """Check if Redis connection is healthy"""
        if not self.redis_client:
            return False
        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False
    
    async def get_state(self, athlete_id: int) -> Optional[AthleteState]:
        """
        Get athlete state with priority:
        1. Redis cache
        2. PostgreSQL database  
        3. In-memory fallback
        """
        self.last_operation_cached = False
        
        # 1. Try Redis cache
        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(f"athlete:state:{athlete_id}")
                if cached_data:
                    data = json.loads(cached_data)
                    self.last_operation_cached = True
                    print(f"📦 Redis cache HIT for athlete {athlete_id}")
                    return AthleteState.from_dict(data)
            except Exception as e:
                print(f"⚠️ Redis cache read error: {e}")
        
        print(f"📦 Cache MISS for athlete {athlete_id}")
        
        # 2. Try PostgreSQL database
        if self.pg_pool:
            try:
                async with self.pg_pool.acquire() as conn:
                    # Get athlete data
                    athlete = await conn.fetchrow(
                        "SELECT id, name, training_goal, weekly_hours_available, "
                        "environment_preference, strava_ftp FROM athletes WHERE id = $1",
                        athlete_id
                    )
                    
                    if athlete:
                        # Get state if exists
                        state_row = await conn.fetchrow(
                            "SELECT * FROM athlete_state WHERE athlete_id = $1",
                            athlete_id
                        )
                        
                        if state_row:
                            # Build from existing state
                            state = self._build_state_from_db(dict(state_row), dict(athlete))
                        else:
                            # Create new state
                            state = AthleteState(
                                athlete_id=athlete_id,
                                name=athlete['name'],
                                training_goal=athlete['training_goal'] or "General Fitness",
                                current_ftp=athlete['strava_ftp'],
                                weekly_hours_available=athlete['weekly_hours_available'] or 8,
                                environment_preference=athlete['environment_preference'] or 'mixed'
                            )
                            # Save to database
                            await self._save_to_database(state)
                        
                        # Cache in Redis
                        await self._cache_state(state)
                        return state
                    else:
                        print(f"⚠️ Athlete {athlete_id} not found in database")
                        
            except Exception as e:
                print(f"❌ Database error: {e}")
                # Fall through to in-memory cache
        
        # 3. Fallback to in-memory cache
        if athlete_id in self._fallback_cache:
            self.last_operation_cached = True
            print(f"📦 Fallback cache HIT for athlete {athlete_id}")
            return self._fallback_cache[athlete_id]
        
        # 4. Create new state in fallback
        print(f"🆕 Creating new state for athlete {athlete_id} (fallback)")
        state = AthleteState(
            athlete_id=athlete_id,
            name=f"Athlete {athlete_id}",
            training_goal="General Fitness",
            ctl_42d=65.5,
            atl_7d=72.3,
            tsb=-6.8,
            current_ftp=250,
            needs_macro_review=False,
            acute_fatigue_level="low",
            substitution_count_this_week=0,
            weekly_hours_available=8,
            environment_preference="mixed"
        )
        
        self._fallback_cache[athlete_id] = state
        return state
    
    async def update_state(self, athlete_id: int, updates: Dict[str, Any]) -> bool:
        """Update athlete state in all storage layers"""
        print(f"🔄 Updating state for athlete {athlete_id}: {updates}")
        
        try:
            # Get current state
            state = await self.get_state(athlete_id)
            if not state:
                return False
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(state, key):
                    setattr(state, key, value)
            
            state.updated_at = datetime.now()
            
            # Save to all storage layers
            success = True
            
            # Save to PostgreSQL
            if self.pg_pool:
                pg_success = await self._save_to_database(state)
                success = success and pg_success
            
            # Save to Redis
            if self.redis_client:
                redis_success = await self._cache_state(state)
                success = success and redis_success
            
            # Save to fallback cache
            self._fallback_cache[athlete_id] = state
            
            return success
            
        except Exception as e:
            print(f"❌ Update state error: {e}")
            return False
    
    async def log_coaching_event(
        self,
        athlete_id: int,
        event_type: str,
        trigger: Optional[str] = None,
        decision: Optional[str] = None,
        rationale: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log coaching event to database"""
        print(f"📝 Logging coaching event: {event_type} for athlete {athlete_id}")
        
        # Try PostgreSQL first
        if self.pg_pool:
            try:
                async with self.pg_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO coaching_events 
                        (athlete_id, event_type, trigger, decision, rationale, metadata, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, NOW())
                    """, athlete_id, event_type, trigger, decision, rationale, json.dumps(metadata or {}))
                    print(f"✅ Event logged to database: {event_type}")
                    return True
            except Exception as e:
                print(f"⚠️ Failed to log to database: {e}")
                # Fall through to console log
        
        # Fallback: just log to console
        print(f"📝 Event (console): athlete={athlete_id}, type={event_type}, "
              f"trigger={trigger}, decision={decision}")
        return True
    
    # Private helper methods
    def _build_state_from_db(self, state_data: dict, athlete_data: dict) -> AthleteState:
        """Build AthleteState from database rows"""
        # Extract from time_availability_profile JSONB
        time_profile = {
            "weekly_hours_available": 8,  # Default
            "environment_preference": 'mixed'  # Default
        }
        
        if state_data.get('time_availability_profile'):
            try:
                profile = state_data['time_availability_profile']
                if isinstance(profile, str):
                    profile = json.loads(profile)
                time_profile.update(profile)
            except Exception as e:
                print(f"⚠️ Error parsing time profile: {e}")
        
        # Use athlete's FTP if available
        current_ftp = athlete_data.get('strava_ftp')
        if not current_ftp and state_data.get('current_ftp'):
            current_ftp = state_data['current_ftp']
        
        # Build state dictionary
        data = {
            "athlete_id": athlete_data['id'],
            "name": athlete_data.get('name', ''),
            "training_goal": athlete_data.get('training_goal', ''),
            "performance_metrics": {
                "ctl_42d": state_data.get('ctl_42d', 0.0),
                "atl_7d": state_data.get('atl_7d', 0.0),
                "tsb": state_data.get('tsb', 0.0),
                "current_ftp": current_ftp
            },
            "adaptation_state": {
                "needs_macro_review": state_data.get('needs_macro_review', False),
                "acute_fatigue_level": state_data.get('acute_fatigue_level', 'low'),
                "substitution_count_this_week": state_data.get('substitution_count_this_week', 0)
            },
            "time_availability": time_profile,
            "metadata": {
                "created_at": state_data.get('created_at', datetime.now()).isoformat(),
                "updated_at": state_data.get('updated_at', datetime.now()).isoformat()
            }
        }
        
        return AthleteState.from_dict(data)
    
    async def _cache_state(self, state: AthleteState) -> bool:
        """Cache state in Redis"""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.setex(
                f"athlete:state:{state.athlete_id}",
                DatabaseConfig.REDIS_TTL,
                state.to_json()
            )
            return True
        except Exception as e:
            print(f"⚠️ Redis cache write error: {e}")
            return False
    
    async def _save_to_database(self, state: AthleteState) -> bool:
        """Save state to PostgreSQL - matches actual table structure"""
        if not self.pg_pool:
            return False
        
        try:
            async with self.pg_pool.acquire() as conn:
                # Check if athlete_state record exists
                exists = await conn.fetchval(
                    "SELECT 1 FROM athlete_state WHERE athlete_id = $1",
                    state.athlete_id
                )
                
                time_profile = json.dumps({
                    "weekly_hours_available": state.weekly_hours_available,
                    "environment_preference": state.environment_preference
                })
                
                if exists:
                    # Update existing
                    await conn.execute("""
                        UPDATE athlete_state SET
                            ctl_42d = $2,
                            atl_7d = $3,
                            tsb = $4,
                            needs_macro_review = $5,
                            acute_fatigue_level = $6,
                            substitution_count_this_week = $7,
                            time_availability_profile = $8,
                            updated_at = $9
                        WHERE athlete_id = $1
                    """,
                    state.athlete_id,
                    state.ctl_42d,
                    state.atl_7d,
                    state.tsb,
                    state.needs_macro_review,
                    state.acute_fatigue_level,
                    state.substitution_count_this_week,
                    time_profile,
                    state.updated_at
                    )
                else:
                    # Insert new
                    await conn.execute("""
                        INSERT INTO athlete_state 
                        (athlete_id, ctl_42d, atl_7d, tsb, needs_macro_review,
                         acute_fatigue_level, substitution_count_this_week,
                         time_availability_profile, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    state.athlete_id,
                    state.ctl_42d,
                    state.atl_7d,
                    state.tsb,
                    state.needs_macro_review,
                    state.acute_fatigue_level,
                    state.substitution_count_this_week,
                    time_profile,
                    state.created_at,
                    state.updated_at
                    )
                
                return True
                
        except Exception as e:
            print(f"❌ Database save error: {e}")
            return False

# Global manager instance
manager = AthleteStateManager()
