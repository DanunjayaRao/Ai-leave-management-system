import pandas as pd
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import LeaveDatabase

def test_database_operations():
    """Test database operations directly"""
    try:
        db = LeaveDatabase()
        
        print("🔍 TESTING DATABASE OPERATIONS...")
        
        # Test adding a leave request
        success = db.add_leave_request(
            user_id=1001,
            leave_date='2025-10-28 00:00:00',
            leave_type='EL',
            reason='Test application',
            duration='Full Day'
        )
        
        print(f"✅ Add leave request result: {success}")
        
        # Check if it was added
        df = pd.read_excel(db.file_path, sheet_name='Hierarchy')
        print(f"✅ Hierarchy sheet now has {len(df)} rows")
        
        if len(df) > 0:
            print("📋 Latest row:")
            print(df.tail(1).to_dict('records'))
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_operations()