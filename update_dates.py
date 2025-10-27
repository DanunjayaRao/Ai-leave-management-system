import pandas as pd
from datetime import datetime, timedelta
from database import LeaveDatabase
import os

def update_dates_to_current():
    """Update all dates in the database to current dates"""
    try:
        db = LeaveDatabase()
        
        # Read the existing data
        df_hierarchy = pd.read_excel(db.file_path, sheet_name='Hierarchy')
        df_used = pd.read_excel(db.file_path, sheet_name='Used')
        
        # Get current date
        today = datetime.now()
        
        # Update Hierarchy sheet dates (pending requests - future dates)
        if not df_hierarchy.empty:
            # For pending requests, set dates to tomorrow and beyond
            for i in range(len(df_hierarchy)):
                if df_hierarchy.loc[i, 'Status'] == 'Pending':
                    # Set leave dates to future (tomorrow + i days)
                    new_leave_date = today + timedelta(days=i+1)
                    df_hierarchy.loc[i, 'Leave_Date'] = new_leave_date.strftime('%Y-%m-%d 00:00:00')
                    
                    # Set applied dates to past (today - i days)
                    new_applied_date = today - timedelta(days=i+1)
                    df_hierarchy.loc[i, 'AppliedDate'] = new_applied_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Update Used sheet dates (past approved leaves)
        if not df_used.empty:
            for i in range(len(df_used)):
                # Set used leave dates to past (today - i-10 days)
                new_used_date = today - timedelta(days=10-i)
                df_used.loc[i, 'Leave_Date'] = new_used_date.strftime('%Y-%m-%d 00:00:00')
        
        # Save the updated data back to Excel
        with pd.ExcelWriter(db.file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df_hierarchy.to_excel(writer, sheet_name='Hierarchy', index=False)
            df_used.to_excel(writer, sheet_name='Used', index=False)
        
        print("✅ Dates updated successfully to current dates!")
        print(f"Today's date: {today.strftime('%Y-%m-%d')}")
        print("Pending requests now have dates from tomorrow onwards")
        
    except Exception as e:
        print(f"❌ Error updating dates: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_dates_to_current()