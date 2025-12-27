"""
AthleteState core data model - SIMPLIFIED VERSION
We'll add cycling metrics later after basic service works
"""
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List

@dataclass
class AthleteState:
    """
    SIMPLIFIED AthleteState model - basic functionality first
    """
    athlete_id: int
    name: str = ""
    training_goal: str = ""
    
    # Basic performance metrics
    ctl_42d: float = 0.0
    atl_7d: float = 0.0
    tsb: float = 0.0
    current_ftp: Optional[int] = None
    
    # Basic adaptation state
    needs_macro_review: bool = False
    acute_fatigue_level: str = "low"
    substitution_count_this_week: int = 0
    
    # Time availability
    weekly_hours_available: int = 0
    environment_preference: str = "mixed"
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "athlete_id": self.athlete_id,
            "name": self.name,
            "training_goal": self.training_goal,
            "performance_metrics": {
                "ctl_42d": self.ctl_42d,
                "atl_7d": self.atl_7d,
                "tsb": self.tsb,
                "current_ftp": self.current_ftp
            },
            "adaptation_state": {
                "needs_macro_review": self.needs_macro_review,
                "acute_fatigue_level": self.acute_fatigue_level,
                "substitution_count_this_week": self.substitution_count_this_week
            },
            "time_availability": {
                "weekly_hours_available": self.weekly_hours_available,
                "environment_preference": self.environment_preference
            },
            "metadata": {
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat()
            }
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AthleteState":
        """Create from dictionary"""
        metrics = data.get("performance_metrics", {})
        adaptation = data.get("adaptation_state", {})
        time_avail = data.get("time_availability", {})
        metadata = data.get("metadata", {})
        
        # Parse dates
        created_at = datetime.now()
        updated_at = datetime.now()
        
        if metadata.get("created_at"):
            try:
                created_at = datetime.fromisoformat(metadata["created_at"].replace('Z', '+00:00'))
            except:
                pass
        
        if metadata.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(metadata["updated_at"].replace('Z', '+00:00'))
            except:
                pass
        
        return cls(
            athlete_id=data["athlete_id"],
            name=data.get("name", ""),
            training_goal=data.get("training_goal", ""),
            ctl_42d=metrics.get("ctl_42d", 0.0),
            atl_7d=metrics.get("atl_7d", 0.0),
            tsb=metrics.get("tsb", 0.0),
            current_ftp=metrics.get("current_ftp"),
            needs_macro_review=adaptation.get("needs_macro_review", False),
            acute_fatigue_level=adaptation.get("acute_fatigue_level", "low"),
            substitution_count_this_week=adaptation.get("substitution_count_this_week", 0),
            weekly_hours_available=time_avail.get("weekly_hours_available", 0),
            environment_preference=time_avail.get("environment_preference", "mixed"),
            created_at=created_at,
            updated_at=updated_at
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "AthleteState":
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def update(self, **kwargs):
        """Update fields"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()
        return self
    
    def __str__(self):
        return f"AthleteState(id={self.athlete_id}, CTL={self.ctl_42d:.1f}, TSB={self.tsb:.1f})"
