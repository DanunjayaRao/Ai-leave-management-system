import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import LeaveDatabase

def check_excel_data():
    """Check what's actually in the Excel file"""
    try:
        db = LeaveDatabase()
        
        print("🔍 CHECKING EXCEL DATA STRUCTURE")
        print("=" * 50)
        
        # Check Available sheet
        print("\n📊 AVAILABLE SHEET:")
        df_available = pd.read_excel(db.file_path, sheet_name='Available')
        print(f"Rows: {len(df_available)}")
        print("Columns:", df_available.columns.tolist())
        if len(df_available) > 0:
            print("Sample data:")
            print(df_available[['UserId', 'Admin ID']].head())
        
        # Check Hierarchy sheet
        print("\n📋 HIERARCHY SHEET:")
        df_hierarchy = pd.read_excel(db.file_path, sheet_name='Hierarchy')
        print(f"Rows: {len(df_hierarchy)}")
        print("Columns:", df_hierarchy.columns.tolist())
        if len(df_hierarchy) > 0:
            print("All requests:")
            for i, row in df_hierarchy.iterrows():
                print(f"  Row {i}: User={row['UserId']}, Admin={row.get('Admin ID', 'N/A')}, Status={row['Status']}, Date={row['Leave_Date']}")
        
        # Check specific admin requests
        print("\n🔍 CHECKING ADMIN 5000 REQUESTS:")
        admin_5000_requests = df_hierarchy[df_hierarchy['Admin ID'] == 5000]
        print(f"Total requests for admin 5000: {len(admin_5000_requests)}")
        
        pending_5000 = admin_5000_requests[admin_5000_requests['Status'] == 'Pending']
        print(f"Pending requests for admin 5000: {len(pending_5000)}")
        
        if len(pending_5000) > 0:
            print("Pending requests details:")
            for i, row in pending_5000.iterrows():
                print(f"  - User {row['UserId']} on {row['Leave_Date']}")
        
        print("\n🔍 CHECKING ADMIN 8001 REQUESTS:")
        admin_8001_requests = df_hierarchy[df_hierarchy['Admin ID'] == 8001]
        print(f"Total requests for admin 8001: {len(admin_8001_requests)}")
        
        pending_8001 = admin_8001_requests[admin_8001_requests['Status'] == 'Pending']
        print(f"Pending requests for admin 8001: {len(pending_8001)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_excel_data()