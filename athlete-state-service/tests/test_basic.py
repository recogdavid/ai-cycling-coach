"""
Basic test of AthleteState class
"""
import sys
import os

# Add the athlete_state directory to Python path
athlete_state_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, athlete_state_path)

try:
    from models import AthleteState
    print("✅ Successfully imported AthleteState")
    
    # Test basic creation
    state = AthleteState(
        athlete_id=123,
        name="Test Athlete",
        training_goal="Sub-3 Marathon",
        ctl_42d=65.5,
        atl_7d=72.3,
        tsb=-6.8
    )
    
    print(f"✅ Created AthleteState: {state}")
    print(f"  Athlete ID: {state.athlete_id}")
    print(f"  Name: {state.name}")
    print(f"  Goal: {state.training_goal}")
    print(f"  CTL: {state.ctl_42d}, ATL: {state.atl_7d}, TSB: {state.tsb}")
    
    print("\n" + "="*50)
    print("✅ All tests passed!")
    print("="*50)
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print(f"Python path: {sys.path}")
except Exception as e:
    print(f"❌ Test failed: {e}")
