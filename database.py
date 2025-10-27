import pandas as pd
import os
from datetime import datetime, timedelta
from config import Config

class LeaveDatabase:
    def __init__(self, file_path=None):
        self.file_path = file_path or Config.EXCEL_FILE
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Ensure the Excel file exists with required sheets"""
        if not os.path.exists(self.file_path):
            print(f"Creating new Excel file at: {self.file_path}")
            self._create_new_excel_file()
        else:
            print(f"Excel file found at: {self.file_path}")
    
    def _create_new_excel_file(self):
        """Create a new Excel file with all required sheets"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # Available sheet with actual balances from your Excel data
            available_data = {
                'UserId': [1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010],
                'EL': [8, 4, 1, 2, 2, 7, 2, 0, 4, 2, 0],
                'SL': [1, 5, 1, 1, 6, 2, 4, 3, 6, 3, 0],
                'CL': [0, 3, 2, 2, 0, 0, 4, 5, 4, 2, 0],
                'TL': [9, 12, 4, 5, 8, 9, 10, 8, 14, 7, 0],
                'Admin ID': [5000, 5000, 5000, 8001, 8001, 8001, 8001, 6099, 6099, 6099, 6099],
                'JoinDate': [
                    (datetime.now().date() - timedelta(days=365)).strftime('%Y-%m-%d'),
                    (datetime.now().date() - timedelta(days=200)).strftime('%Y-%m-%d'),
                    (datetime.now().date() - timedelta(days=100)).strftime('%Y-%m-%d'),
                    (datetime.now().date() - timedelta(days=50)).strftime('%Y-%m-%d'),
                    (datetime.now().date() - timedelta(days=80)).strftime('%Y-%m-%d'),
                    (datetime.now().date() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    (datetime.now().date() - timedelta(days=120)).strftime('%Y-%m-%d'),
                    (datetime.now().date() - timedelta(days=150)).strftime('%Y-%m-%d'),
                    (datetime.now().date() - timedelta(days=180)).strftime('%Y-%m-%d'),
                    (datetime.now().date() - timedelta(days=95)).strftime('%Y-%m-%d'),
                    (datetime.now().date() - timedelta(days=20)).strftime('%Y-%m-%d')
                ]
            }
            
            # Used sheet - past approved leaves
            used_data = {
                'UserId': [1000, 1000, 1009, 1000, 1002, 1002, 1001, 1004, 1006, 1006, 1006, 1006, 1008, 1008, 1008],
                'Leave_Date': [
                    (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d 00:00:00'),
                    (datetime.now() - timedelta(days=9)).strftime('%Y-%m-%d 00:00:00'),
                    (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d 00:00:00'),
                    (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d 00:00:00'),
                    (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d 00:00:00'),
                    (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d 00:00:00'),
                    (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d 00:00:00'),
                    (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d 00:00:00'),
                    (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d 00:00:00'),
                    (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d 00:00:00'),
                    (datetime.now() - timedelta(days=13)).strftime('%Y-%m-%d 00:00:00'),
                    (datetime.now() - timedelta(days=12)).strftime('%Y-%m-%d 00:00:00'),
                    (datetime.now() - timedelta(days=11)).strftime('%Y-%m-%d 00:00:00'),
                    (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d 00:00:00'),
                    (datetime.now() - timedelta(days=9)).strftime('%Y-%m-%d 00:00:00')
                ],
                'LeaveType': ['EL', 'CL', 'SL', 'SL', 'SL', 'EL', 'SL', 'SL', 'EL', 'EL', 'EL', 'EL', 'EL', 'EL', 'EL'],
                'Duration': ['Full Day', 'Half Day', 'Full Day', 'Full Day', 'Full Day', 'Full Day', 'Full Day', 'Full Day', 'Full Day', 'Full Day', 'Full Day', 'Full Day', 'Full Day', 'Full Day', 'Full Day']
            }
            
            # Hierarchy sheet with CURRENT pending requests (future dates)
            today = datetime.now()
            hierarchy_data = {
                'Admin ID': [5000, 5000, 8001, 6099, 5000, 8001],
                'UserId': [1001, 1002, 1004, 1009, 1000, 1006],
                'Leave_Date': [
                    (today + timedelta(days=2)).strftime('%Y-%m-%d 00:00:00'),  # Day after tomorrow
                    (today + timedelta(days=3)).strftime('%Y-%m-%d 00:00:00'),  # In 3 days
                    (today + timedelta(days=5)).strftime('%Y-%m-%d 00:00:00'),  # In 5 days
                    (today + timedelta(days=7)).strftime('%Y-%m-%d 00:00:00'),  # In 7 days
                    (today + timedelta(days=1)).strftime('%Y-%m-%d 00:00:00'),  # Tomorrow
                    (today + timedelta(days=4)).strftime('%Y-%m-%d 00:00:00')   # In 4 days
                ],
                'Status': ['Pending', 'Pending', 'Pending', 'Pending', 'Pending', 'Pending'],
                'LeaveType': ['EL', 'SL', 'CL', 'EL', 'SL', 'CL'],
                'Reason': ['Family vacation', 'Medical appointment', 'Personal work', 'Wedding function', 'Dental checkup', 'Family emergency'],
                'AppliedDate': [
                    (today - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                    (today - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'),
                    (today - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                    (today - timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S'),
                    today.strftime('%Y-%m-%d %H:%M:%S'),
                    (today - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
                ],
                'Duration': ['Full Day', 'Full Day', 'Full Day', 'Full Day', 'Half Day', 'Full Day']
            }
            
            # ChatHistory sheet with sample data
            chat_data = {
                'UserID': [1000, 1000, 1002, 1002, 1001, 1001, 1001, 1001, 1001, 1001],
                'Role': ['user', 'assistant', 'user', 'assistant', 'user', 'assistant', 'user', 'assistant', 'user', 'assistant'],
                'Message': [
                    'hi',
                    'Hello! I\'m your AI leave management assistant. How can I help you with leave policies, applications, or balances today?',
                    'hi', 
                    'Hello! I\'m your AI leave management assistant. How can I help you with leave policies, applications, or balances today?',
                    'hi',
                    'Hello! I\'m your AI leave management assistant. How can I help you with leave policies, applications, or balances today?',
                    'hi',
                    'Hello! I\'m your AI leave management assistant. How can I help you with leave policies, applications, or balances today?',
                    'i want to apply SL tomorrow',
                    '❌ SL Date Restriction: Sick Leave cannot be applied for future dates.'
                ],
                'Timestamp': [
                    (today - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
                    (today - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
                    (today - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
                    (today - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'), 
                    (today - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
                    (today - timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
                    (today - timedelta(minutes=20)).strftime('%Y-%m-%d %H:%M:%S'),
                    (today - timedelta(minutes=20)).strftime('%Y-%m-%d %H:%M:%S'),
                    (today - timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S'),
                    (today - timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
                ]
            }
            
            # Create Excel file with all sheets
            with pd.ExcelWriter(self.file_path, engine='openpyxl') as writer:
                pd.DataFrame(available_data).to_excel(writer, sheet_name='Available', index=False)
                pd.DataFrame(used_data).to_excel(writer, sheet_name='Used', index=False)
                pd.DataFrame(hierarchy_data).to_excel(writer, sheet_name='Hierarchy', index=False)
                pd.DataFrame(chat_data).to_excel(writer, sheet_name='ChatHistory', index=False)
            
            print("✅ Excel file created successfully with current sample data!")
            
        except Exception as e:
            print(f"❌ Error creating Excel file: {e}")
            import traceback
            traceback.print_exc()
    
    def get_user_balance(self, user_id):
        """Get leave balance for a user - REMOVED ELIGIBILITY CHECK"""
        try:
            df = pd.read_excel(self.file_path, sheet_name='Available')
            user_data = df[df['UserId'] == int(user_id)]
            
            if not user_data.empty:
                el = user_data['EL'].iloc[0]
                sl = user_data['SL'].iloc[0]
                cl = user_data['CL'].iloc[0]
                tl = user_data['TL'].iloc[0]
                
                return {
                    'EL': int(el) if not pd.isna(el) else 0,
                    'SL': int(sl) if not pd.isna(sl) else 0,
                    'CL': int(cl) if not pd.isna(cl) else 0,
                    'TL': int(tl) if not pd.isna(tl) else 0,
                    'eligible': True  # Always eligible now
                }
            return None
        except Exception as e:
            print(f"Error reading balance for user {user_id}: {e}")
            return None

    def update_user_balance(self, user_id, leave_type, days):
        """Update user's leave balance"""
        try:
            df = pd.read_excel(self.file_path, sheet_name='Available')
            user_index = df[df['UserId'] == int(user_id)].index
            
            if not user_index.empty:
                idx = user_index[0]
                current_balance = df.at[idx, leave_type]
                
                if current_balance >= days:
                    df.at[idx, leave_type] = current_balance - days
                    # Update total leaves (sum of EL + SL + CL)
                    df.at[idx, 'TL'] = df.at[idx, 'EL'] + df.at[idx, 'SL'] + df.at[idx, 'CL']
                    
                    with pd.ExcelWriter(self.file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                        df.to_excel(writer, sheet_name='Available', index=False)
                    return True
            return False
        except Exception as e:
            print(f"Error updating balance: {e}")
            return False

    def add_leave_request(self, user_id, leave_date, leave_type, reason, duration="Full Day"):
        """Add a new leave request - WITH FILE LOCK HANDLING"""
        try:
            print(f"💾 ADD_LEAVE_REQUEST: user={user_id}, date={leave_date}, type={leave_type}")
            
            # Get admin ID for the user
            df_available = pd.read_excel(self.file_path, sheet_name='Available')
            user_data = df_available[df_available['UserId'] == int(user_id)]
            
            if user_data.empty:
                print(f"❌ User {user_id} not found in Available sheet")
                return False
            
            admin_id = int(user_data['Admin ID'].iloc[0])
            print(f"✅ Found admin ID: {admin_id}")
            
            # Read existing hierarchy data with error handling
            try:
                df_hierarchy = pd.read_excel(self.file_path, sheet_name='Hierarchy')
                print(f"✅ Read Hierarchy sheet: {len(df_hierarchy)} rows")
            except Exception as e:
                print(f"❌ Error reading Hierarchy, creating new: {e}")
                df_hierarchy = pd.DataFrame(columns=['Admin ID', 'UserId', 'Leave_Date', 'Status', 'LeaveType', 'Reason', 'AppliedDate', 'Duration'])
            
            # Add new request
            new_request = {
                'Admin ID': admin_id,
                'UserId': int(user_id),
                'Leave_Date': leave_date,
                'Status': 'Pending',
                'LeaveType': leave_type,
                'Reason': reason,
                'AppliedDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Duration': duration
            }
            
            print(f"💾 New request data: {new_request}")
            
            df_hierarchy = pd.concat([df_hierarchy, pd.DataFrame([new_request])], ignore_index=True)
            print(f"✅ DataFrame updated: {len(df_hierarchy)} rows")
            
            # Update Excel file with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with pd.ExcelWriter(self.file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                        df_hierarchy.to_excel(writer, sheet_name='Hierarchy', index=False)
                    print("✅ Excel file updated successfully")
                    return True
                except PermissionError:
                    if attempt < max_retries - 1:
                        print(f"⚠️ File locked, retrying... ({attempt + 1}/{max_retries})")
                        import time
                        time.sleep(1)  # Wait 1 second before retry
                    else:
                        print("❌ File still locked after retries")
                        return False
                except Exception as e:
                    print(f"❌ Error writing to Excel: {e}")
                    return False
            
        except Exception as e:
            print(f"❌ Error in add_leave_request: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_user_leave_requests(self, user_id):
        """Get all leave requests for a user"""
        try:
            df = pd.read_excel(self.file_path, sheet_name='Hierarchy')
            user_requests = df[df['UserId'] == int(user_id)]
            return user_requests.to_dict('records')
        except Exception as e:
            print(f"Error reading leave requests: {e}")
            return []

    def get_pending_requests(self, admin_id):
        """Get pending leave requests for an admin - WITH BETTER ERROR HANDLING"""
        try:
            print(f"🔍 Getting pending requests for admin: {admin_id} (type: {type(admin_id)})")
            
            df = pd.read_excel(self.file_path, sheet_name='Hierarchy')
            
            if df.empty:
                print("❌ Hierarchy sheet is empty")
                return []
            
            # Ensure admin_id is integer for comparison
            try:
                admin_id_int = int(admin_id)
            except ValueError:
                print(f"❌ Invalid admin ID format: {admin_id}")
                return []
            
            # Convert Admin ID column to int for proper comparison
            df['Admin ID'] = df['Admin ID'].astype(int)
            
            pending = df[(df['Admin ID'] == admin_id_int) & (df['Status'] == 'Pending')]
            
            print(f"✅ Found {len(pending)} pending requests for admin {admin_id_int}")
            
            # Convert to list of dictionaries with proper data types
            result = []
            for _, row in pending.iterrows():
                result.append({
                    'UserId': int(row['UserId']),
                    'Leave_Date': str(row['Leave_Date']),
                    'LeaveType': str(row['LeaveType']),
                    'Reason': str(row['Reason']),
                    'AppliedDate': str(row['AppliedDate']),
                    'Duration': str(row['Duration']),
                    'Admin ID': int(row['Admin ID'])
                })
            
            return result
            
        except Exception as e:
            print(f"❌ Error in get_pending_requests: {e}")
            import traceback
            traceback.print_exc()
            return []

    def update_leave_status(self, user_id, leave_date, status):
        """Update leave request status - FIXED VERSION"""
        try:
            print(f"🔍 DB: Updating status - user={user_id}, date={leave_date}, status={status}")
            
            df = pd.read_excel(self.file_path, sheet_name='Hierarchy')
            
            # Find the matching request
            mask = (df['UserId'] == int(user_id)) & (df['Leave_Date'] == leave_date)
            
            if mask.any():
                df.loc[mask, 'Status'] = status
                
                # If approved, update balance and add to used leaves
                if status == 'Approved':
                    leave_type = df.loc[mask, 'LeaveType'].iloc[0]
                    
                    # Update balance
                    balance_success = self.update_user_balance(user_id, leave_type, 1)
                    if not balance_success:
                        print(f"❌ Failed to update balance for user {user_id}")
                        return False
                    
                    # Add to Used sheet
                    try:
                        df_used = pd.read_excel(self.file_path, sheet_name='Used')
                    except:
                        df_used = pd.DataFrame(columns=['UserId', 'Leave_Date', 'LeaveType', 'Duration'])
                    
                    new_used = {
                        'UserId': int(user_id),
                        'Leave_Date': leave_date,
                        'LeaveType': leave_type,
                        'Duration': df.loc[mask, 'Duration'].iloc[0]
                    }
                    df_used = pd.concat([df_used, pd.DataFrame([new_used])], ignore_index=True)
                    
                    # Save both sheets
                    with pd.ExcelWriter(self.file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                        df.to_excel(writer, sheet_name='Hierarchy', index=False)
                        df_used.to_excel(writer, sheet_name='Used', index=False)
                else:
                    # Just update the status for rejected leaves
                    with pd.ExcelWriter(self.file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                        df.to_excel(writer, sheet_name='Hierarchy', index=False)
                
                print(f"✅ DB: Successfully updated status to {status}")
                return True
            else:
                print(f"❌ DB: No matching request found for user {user_id} on {leave_date}")
                return False
                
        except Exception as e:
            print(f"❌ DB Error updating leave status: {e}")
            return False

    def approve_all_pending(self, admin_id):
        """Approve all pending requests for an admin - FIXED"""
        try:
            print(f"🔍 Starting approve_all_pending for admin: {admin_id}")
            
            pending_requests = self.get_pending_requests(admin_id)
            print(f"🔍 Processing {len(pending_requests)} requests")
            
            if len(pending_requests) == 0:
                print("❌ No pending requests found to approve")
                return 0, 0
            
            approved_count = 0
            
            for request in pending_requests:
                print(f"🔍 Approving: User {request['UserId']} on {request['Leave_Date']}")
                
                success = self.update_leave_status(
                    request['UserId'], 
                    request['Leave_Date'], 
                    'Approved'
                )
                
                if success:
                    approved_count += 1
                    print(f"✅ Approved successfully ({approved_count}/{len(pending_requests)})")
                else:
                    print(f"❌ Failed to approve User {request['UserId']}")
            
            print(f"✅ FINAL: Approved {approved_count}/{len(pending_requests)}")
            return approved_count, len(pending_requests)
            
        except Exception as e:
            print(f"❌ Error in approve_all_pending: {e}")
            return 0, 0

    def check_date_overlap(self, user_id, leave_date):
        """Check if leave date overlaps with existing leaves"""
        try:
            df_hierarchy = pd.read_excel(self.file_path, sheet_name='Hierarchy')
            df_used = pd.read_excel(self.file_path, sheet_name='Used')
            
            leave_date_dt = pd.to_datetime(leave_date).date()
            
            # Check in hierarchy (approved and pending)
            user_leaves = df_hierarchy[df_hierarchy['UserId'] == int(user_id)]
            for _, leave in user_leaves.iterrows():
                existing_date = pd.to_datetime(leave['Leave_Date']).date()
                if existing_date == leave_date_dt and leave['Status'] != 'Rejected':
                    return True
            
            # Check in used leaves
            user_used = df_used[df_used['UserId'] == int(user_id)]
            for _, used in user_used.iterrows():
                existing_date = pd.to_datetime(used['Leave_Date']).date()
                if existing_date == leave_date_dt:
                    return True
            
            return False
        except Exception as e:
            print(f"Error checking date overlap: {e}")
            return True
        
    def save_chat_message(self, user_id, role, message, timestamp=None):
        """Save a chat message to the database"""
        try:
            # Create ChatHistory sheet if it doesn't exist
            try:
                df_chat = pd.read_excel(self.file_path, sheet_name='ChatHistory')
            except:
                # Create new ChatHistory sheet
                df_chat = pd.DataFrame(columns=['UserID', 'Role', 'Message', 'Timestamp'])
            
            if timestamp is None:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            new_message = {
                'UserID': int(user_id),
                'Role': role,  # 'user' or 'assistant'
                'Message': message,
                'Timestamp': timestamp
            }
            
            df_chat = pd.concat([df_chat, pd.DataFrame([new_message])], ignore_index=True)
            
            # Update Excel file
            with pd.ExcelWriter(self.file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df_chat.to_excel(writer, sheet_name='ChatHistory', index=False)
            
            return True
        except Exception as e:
            print(f"Error saving chat message: {e}")
            return False

    def get_chat_history(self, user_id, limit=50):
        """Get chat history for a user - PROPER GRADIO FORMAT"""
        try:
            df_chat = pd.read_excel(self.file_path, sheet_name='ChatHistory')
            # Filter by user ID to ensure privacy
            user_chats = df_chat[df_chat['UserID'] == int(user_id)]
            user_chats = user_chats.sort_values('Timestamp').tail(limit)
            
            # Convert to list of dictionaries
            records = user_chats.to_dict('records')
            
            print(f"✅ Database: Found {len(records)} chat records for user {user_id}")
            return records
            
        except Exception as e:
            print(f"❌ Database error getting chat history: {e}")
            return []

    def clear_chat_history(self, user_id):
        """Clear chat history for a user - PRIVATE CLEAR"""
        try:
            df_chat = pd.read_excel(self.file_path, sheet_name='ChatHistory')
            # Only remove messages for this specific user
            df_chat = df_chat[df_chat['UserID'] != int(user_id)]
            
            with pd.ExcelWriter(self.file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df_chat.to_excel(writer, sheet_name='ChatHistory', index=False)
            
            return True
        except Exception as e:
            print(f"Error clearing chat history: {e}")
            return False
        
    def is_weekend(self, date):
        """Check if date is weekend (Saturday or Sunday)"""
        return date.weekday() >= 5  # 5=Saturday, 6=Sunday

    def is_public_holiday(self, date):
        """Check if date is a public holiday"""
        from config import Config
        date_str = date.strftime('%Y-%m-%d')
        return date_str in Config.PUBLIC_HOLIDAYS

    def is_valid_working_day(self, date):
        """Check if date is a valid working day (not weekend or holiday)"""
        return not (self.is_weekend(date) or self.is_public_holiday(date))
    
    def is_valid_sl_date(self, date):
        """Check if date is valid for Sick Leave (today or past dates, max 15 days before)"""
        today = datetime.now().date()
        days_diff = (today - date).days
        
        # SL can be for today or past dates, maximum 15 days before
        return date <= today and days_diff <= 15