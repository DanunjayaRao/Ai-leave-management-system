import gradio as gr
import pandas as pd
from datetime import datetime, timedelta
import os
import sys
import re
from chatbot_enhanced import EnhancedLeaveChatbot

# Add current directory to Python path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Now import your modules
from database import LeaveDatabase
from auth import AuthSystem
from config import Config

# Initialize systems
print("🚀 Initializing AI Leave Management System...")

class SimpleLeaveAgent:
    def __init__(self, db):
        self.db = db
        # We'll use database for persistent storage instead of memory
    
    def get_chat_history(self, user_id):
        """Get chat history from database for persistent storage"""
        try:
            # Load from database - this ensures persistence across page refreshes
            db_history = self.db.get_chat_history(user_id)
            
            # Convert database format to Gradio format
            gradio_history = []
            current_user_msg = None
            
            for record in db_history:
                if record['Role'] == 'user':
                    current_user_msg = record['Message']
                elif record['Role'] == 'assistant' and current_user_msg is not None:
                    gradio_history.append([current_user_msg, record['Message']])
                    current_user_msg = None
            
            print(f"✅ Loaded {len(gradio_history)} chat messages for user {user_id}")
            return gradio_history
            
        except Exception as e:
            print(f"❌ Error loading chat history: {e}")
            return []
    
    def process_message(self, user_id, message):
        """Process user message and return response - WITH COMPLETE DEBUG"""
        print(f"🔍 PROCESS_MESSAGE START: user_id={user_id}, message='{message}'")
        
        try:
            # Save user message to database FIRST for persistence
            print("💾 Saving user message to database...")
            save_success = self.db.save_chat_message(user_id, 'user', message)
            print(f"💾 Save result: {save_success}")
            
            # Generate response
            print("🤖 Generating response...")
            response = self._generate_response(user_id, message)
            print(f"🤖 Response generated: {response[:100]}...")
            
            # Save assistant response to database for persistence
            print("💾 Saving bot response to database...")
            save_success = self.db.save_chat_message(user_id, 'assistant', response)
            print(f"💾 Save result: {save_success}")
            
            print("✅ PROCESS_MESSAGE COMPLETED SUCCESSFULLY")
            return response
            
        except Exception as e:
            print(f"❌ ERROR in process_message: {str(e)}")
            import traceback
            traceback.print_exc()
            return "I apologize, but I'm having trouble processing your request right now. Please try again."
    
    def _generate_response(self, user_id, message):
        """Generate response based on message content - WITH CONVERSATION MEMORY"""
        print(f"🔍 _generate_response: user_id={user_id}, message='{message}'")
        
        try:
            message_lower = message.lower().strip()
            print(f"🔍 Processing message: '{message_lower}'")
            
            # Get recent chat history for context
            recent_history = self.db.get_chat_history(user_id, limit=5)
            
            # Check if this is a continuation of previous conversation
            is_continuation = self._is_continuation(message_lower, recent_history)
            
            if is_continuation:
                print("✅ Detected continuation of previous conversation")
                return self._handle_continuation(user_id, message, recent_history)
            
            # Handle leave applications FIRST (most important)
            if any(word in message_lower for word in ['apply', 'application', 'request', 'want to apply', 'need leave', 'i want', 'can i apply', 'apply leave']):
                print("✅ Detected leave application request")
                return self._handle_leave_application(user_id, message)
            
            # Handle balance inquiries
            elif any(word in message_lower for word in ['balance', 'remaining', 'available', 'how many', 'leave left']):
                print("✅ Detected balance request")
                balance = self.db.get_user_balance(user_id)
                if balance:
                    return f"""**Your Leave Balance:**\n\n• 🏖️ Earned Leave (EL): {balance['EL']} days\n• 🤒 Sick Leave (SL): {balance['SL']} days\n• 🎯 Casual Leave (CL): {balance['CL']} days\n• 📊 Total Available: {balance['TL']} days"""
                else:
                    return "I couldn't retrieve your leave balance at the moment. Please try again later."
            
            # Handle status inquiries
            elif any(word in message_lower for word in ['status', 'application status', 'my applications', 'pending', 'approved']):
                print("✅ Detected status request")
                requests = self.db.get_user_leave_requests(user_id)
                if requests:
                    status_text = "**Your Leave Applications:**\n\n"
                    for req in requests[-5:]:
                        date_str = req['Leave_Date'].split()[0] if ' ' in str(req['Leave_Date']) else str(req['Leave_Date'])
                        icon = "✅" if req['Status'] == 'Approved' else "❌" if req['Status'] == 'Rejected' else "⏳"
                        status_text += f"• {date_str}: {req['LeaveType']} - {icon} {req['Status']}\n"
                        if req['Reason']:
                            status_text += f"  Reason: {req['Reason']}\n"
                    return status_text
                else:
                    return "You have no leave applications."
            
            # Handle policy inquiries
            elif any(word in message_lower for word in ['policy', 'rule', 'regulation', 'how to', 'can i', 'what is']):
                print("✅ Detected policy request")
                return """**Leave Policies (From Company Rules):**\n
    • **Earned Leave (EL):** 20 days per year (minimum 3 consecutive days)
    • **Sick Leave (SL):** 10 days per year (past dates only)  
    • **Casual Leave (CL):** 10 days per year
    • **Application Rules:**
    - EL: Minimum 3 consecutive working days
    - SL: Past dates only (up to 15 days before)
    - CL: Maximum 2 consecutive days
    - No leaves on weekends or public holidays"""
            
            # Handle greetings
            elif any(word in message_lower for word in ['hello', 'hi', 'hey', 'hola', 'greetings']):
                print("✅ Detected greeting")
                balance = self.db.get_user_balance(user_id)
                if balance:
                    return f"""👋 **Hello! I'm your AI Leave Management Assistant**

    📊 **Your Current Leave Balance:**
    • 🏖️ Earned Leave (EL): {balance['EL']} days
    • 🤒 Sick Leave (SL): {balance['SL']} days  
    • 🎯 Casual Leave (CL): {balance['CL']} days
    • 📈 Total Available: {balance['TL']} days

    How can I help you with leave policies, applications, or balances today?"""
                else:
                    return "Hello! I'm your AI leave management assistant. How can I help you with leave policies, applications, or balances today?"
            
            # Handle help requests
            elif any(word in message_lower for word in ['help', 'what can you do', 'options', 'menu']):
                print("✅ Detected help request")
                return """**I can help you with:**\n
    • 📚 Leave policies and rules
    • 📊 Checking your leave balance  
    • 📝 Applying for leave
    • 📋 Checking application status
    • ❓ Answering leave-related questions

    **Try saying:**
    - \"Apply EL for 3 days from tomorrow\"
    - \"What's my leave balance?\"
    - \"Check my application status\"
    - \"What are the leave policies?\""""
            
            # Handle single leave type responses (like "EL", "SL", "CL")
            elif message_lower in ['el', 'sl', 'cl']:
                print(f"✅ Detected single leave type: {message_lower}")
                return self._handle_single_leave_type(message_lower.upper())
            
            # Default response for unknown queries
            else:
                print("✅ Default response")
                return """**I can help you with leave management!**\n
    Please ask me about:
    • Leave applications (\"Apply EL for 3 days\")
    • Your balance (\"What's my leave balance?\")
    • Application status (\"My application status\")
    • Policy information (\"What are the leave rules?\")\n
    **Need help?** Just type \"help\" for options."""
                
        except Exception as e:
            print(f"❌ ERROR in _generate_response: {str(e)}")
            import traceback
            traceback.print_exc()
            return "I apologize, but I'm having trouble processing your request right now. Please try again."

    def _is_continuation(self, current_message, recent_history):
        """Check if current message is continuation of previous conversation"""
        if not recent_history:
            return False
        
        # Get the last assistant message
        last_assistant_msg = None
        for record in reversed(recent_history):
            if record['Role'] == 'assistant':
                last_assistant_msg = record['Message'].lower()
                break
        
        if not last_assistant_msg:
            return False
        
        # Check if last message was asking for leave type
        if 'specify the type' in last_assistant_msg or 'leave types' in last_assistant_msg:
            return current_message in ['el', 'sl', 'cl']
        
        return False

    def _handle_continuation(self, user_id, message, recent_history):
        """Handle continuation of previous conversation"""
        message_lower = message.lower().strip()
        
        # Get the original user message that triggered the leave type request
        original_message = None
        for record in reversed(recent_history):
            if record['Role'] == 'user' and any(word in record['Message'].lower() for word in ['apply', 'leave']):
                original_message = record['Message']
                break
        
        if original_message and message_lower in ['el', 'sl', 'cl']:
            # Combine the original message with the leave type
            combined_message = f"{original_message} {message_lower.upper()}"
            print(f"✅ Combined message: {combined_message}")
            return self._handle_leave_application(user_id, combined_message)
        
        return "I'm not sure what you're referring to. How can I help you with leave management?"

    def _handle_single_leave_type(self, leave_type):
        """Handle when user just types leave type like EL, SL, CL"""
        leave_info = {
            'EL': """🏖️ **Earned Leave (EL)**
    • For planned vacations
    • Minimum 3 consecutive days required
    • Apply within ±30 days window

    **Try:** "Apply EL for 3 days from tomorrow" or "Apply EL from 25-12-2024 to 27-12-2024\"""",
            
            'SL': """🤒 **Sick Leave (SL)**
    • For medical reasons
    • Can apply for today and past dates
    • Maximum 15 days in past

    **Try:** "Apply SL for today" or "Apply SL for yesterday\"""",
            
            'CL': """🎯 **Casual Leave (CL)**
    • For emergencies
    • Maximum 2 consecutive days
    • Apply within ±30 days window

    **Try:** "Apply CL for tomorrow" or "Apply CL for 2 days\""""
        }
        
        return leave_info.get(leave_type, "Please specify a valid leave type: EL, SL, or CL")

    
    def _clear_chat_history(self, user_id):
        """Clear chat history for user from database"""
        try:
            success = self.db.clear_chat_history(user_id)
            if success:
                return "🗑️ Chat history cleared successfully!"
            else:
                return "❌ Failed to clear chat history"
        except Exception as e:
            return f"❌ Error clearing chat: {str(e)}"
    
    def _parse_natural_language_date(self, date_text, base_date=None):
        """Parse natural language dates like 'last monday', 'day before yesterday' etc."""
        if base_date is None:
            base_date = datetime.now().date()
        
        date_text = date_text.lower().strip()
        
        # Direct mappings
        if date_text in ['today', 'now']:
            return base_date
        elif date_text in ['yesterday']:
            return base_date - timedelta(days=1)
        elif date_text in ['tomorrow']:
            return base_date + timedelta(days=1)
        elif date_text in ['day after tomorrow']:
            return base_date + timedelta(days=2)
        elif date_text in ['day before yesterday']:
            return base_date - timedelta(days=2)
        
        # Last/Next week patterns
        if 'last week' in date_text:
            base_date = base_date - timedelta(days=7)
            date_text = date_text.replace('last week', '').strip()
        elif 'next week' in date_text:
            base_date = base_date + timedelta(days=7)
            date_text = date_text.replace('next week', '').strip()
        
        # Day of week patterns
        days_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6,
            'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
        }
        
        for day_name, day_num in days_map.items():
            if day_name in date_text:
                current_weekday = base_date.weekday()
                
                if 'last' in date_text:
                    # Find the most recent past occurrence
                    days_ago = (current_weekday - day_num) % 7
                    if days_ago == 0:
                        days_ago = 7  # Go back one week
                    return base_date - timedelta(days=days_ago)
                elif 'next' in date_text:
                    # Find the next future occurrence
                    days_ahead = (day_num - current_weekday) % 7
                    if days_ahead == 0:
                        days_ahead = 7  # Go to next week
                    return base_date + timedelta(days=days_ahead)
                else:
                    # Default to next occurrence
                    days_ahead = (day_num - current_weekday) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    return base_date + timedelta(days=days_ahead)
        
        # Relative day patterns
        if 'days ago' in date_text:
            try:
                num_days = int(re.search(r'(\d+)\s+days?\s+ago', date_text).group(1))
                return base_date - timedelta(days=num_days)
            except:
                pass
        elif 'days from now' in date_text or 'days later' in date_text:
            try:
                num_days = int(re.search(r'(\d+)\s+days?\s+(from now|later)', date_text).group(1))
                return base_date + timedelta(days=num_days)
            except:
                pass
        
        return None

    def _extract_dates_from_message(self, message):
        """Extract dates from natural language message with comprehensive parsing"""
        message_lower = message.lower()
        today = datetime.now().date()
        leave_dates = []
        
        print(f"🔍 Parsing dates from: '{message_lower}'")
        
        # Clean the message
        clean_message = message_lower
        remove_phrases = [
            'i want to apply', 'apply for', 'i need', 'want to take', 'take', 
            'leave', 'sl', 'el', 'cl', 'sick', 'earned', 'casual', 'medical',
            'apply', 'for', 'a', 'an', 'the'
        ]
        
        for phrase in remove_phrases:
            clean_message = clean_message.replace(phrase, ' ')
        
        clean_message = ' '.join(clean_message.split()).strip()
        print(f"🔍 Cleaned message: '{clean_message}'")
        
        # Try specific date patterns first (DD-MM-YYYY, DD/MM/YYYY, etc.)
        date_patterns = [
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',  # DD-MM-YYYY
            r'(\d{1,2})[-/](\d{1,2})',             # DD-MM (current year)
            r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',  # YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, clean_message)
            if matches:
                for match in matches:
                    try:
                        if len(match) == 3:  # DD-MM-YYYY or YYYY-MM-DD
                            if len(match[0]) == 4:  # YYYY-MM-DD
                                year, month, day = int(match[0]), int(match[1]), int(match[2])
                            else:  # DD-MM-YYYY
                                day, month, year = int(match[0]), int(match[1]), int(match[2])
                            leave_date = datetime(year, month, day).date()
                            leave_dates.append(leave_date)
                            print(f"✅ Found specific date: {leave_date}")
                        elif len(match) == 2:  # DD-MM (current year)
                            day, month = int(match[0]), int(match[1])
                            year = today.year
                            leave_date = datetime(year, month, day).date()
                            leave_dates.append(leave_date)
                            print(f"✅ Found date (current year): {leave_date}")
                    except ValueError as e:
                        print(f"❌ Date parsing error: {e}")
                        continue
        
        # If no specific dates found, try natural language parsing
        if not leave_dates:
            # Look for natural language date patterns
            natural_patterns = [
                r'(today|tomorrow|yesterday|day after tomorrow|day before yesterday)',
                r'(last|next)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)',
                r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)',
                r'(\d+)\s+days?\s+ago',
                r'(\d+)\s+days?\s+(from now|later)',
                r'last week',
                r'next week'
            ]
            
            for pattern in natural_patterns:
                matches = re.findall(pattern, clean_message)
                if matches:
                    for match in matches:
                        if isinstance(match, tuple):
                            date_text = ' '.join(match).strip()
                        else:
                            date_text = match.strip()
                        
                        parsed_date = self._parse_natural_language_date(date_text, today)
                        if parsed_date:
                            leave_dates.append(parsed_date)
                            print(f"✅ Found natural language date '{date_text}': {parsed_date}")
                            break
                    if leave_dates:
                        break
        
        # If still no dates found, try to extract any remaining date-like phrases
        if not leave_dates:
            # Final attempt with the entire cleaned message
            parsed_date = self._parse_natural_language_date(clean_message, today)
            if parsed_date:
                leave_dates.append(parsed_date)
                print(f"✅ Final natural language parsing: {parsed_date}")
        
        # Remove duplicates and sort
        leave_dates = sorted(list(set(leave_dates)))
        
        print(f"📅 Final parsed dates: {leave_dates}")
        return leave_dates

    def calculate_working_days(self, start_date, num_days):
        """Calculate actual working days excluding weekends and holidays"""
        working_days = []
        current_date = start_date
        days_found = 0
        
        while days_found < num_days:
            if not db.is_weekend(current_date) and not db.is_public_holiday(current_date):
                working_days.append(current_date)
                days_found += 1
            current_date += timedelta(days=1)
        
        return working_days
    
    def _handle_leave_application(self, user_id, message):
        """Handle leave application from chat - FIXED DATE PARSING"""
        print(f"🔍 LEAVE APPLICATION: user_id={user_id}, message='{message}'")
        
        try:
            message_lower = message.lower()
            
            # Leave type detection - more comprehensive
            leave_type = None
            if any(word in message_lower for word in ['el', 'earned']):
                leave_type = 'EL'
            elif any(word in message_lower for word in ['sl', 'sick']):
                leave_type = 'SL'
            elif any(word in message_lower for word in ['cl', 'casual']):
                leave_type = 'CL'
            
            if not leave_type:
                return """**To apply for leave, please specify the type:**\n
    **Leave Types:**
    • EL (Earned Leave) - For planned vacations (minimum 3 consecutive days)
    • SL (Sick Leave) - For medical reasons (past dates only)  
    • CL (Casual Leave) - For emergencies (maximum 2 days)"""
            
            # ========== IMPROVED DATE PARSING ==========
            today = datetime.now().date()
            leave_dates = []
            
            print(f"🔍 Parsing dates from: '{message}'")
            
            # Enhanced date parsing for various formats
            leave_dates = self._extract_dates_improved(message, today)
            
            if not leave_dates:
                return f"""❌ **Could not understand the date in your request**

    I couldn't figure out which date you want to apply {leave_type} for.

    **Please try these formats:**
    • "Apply {leave_type} for today"
    • "Apply {leave_type} for yesterday" 
    • "Apply {leave_type} for 25-09-2025"
    • "Apply {leave_type} for last Monday"
    • "Apply {leave_type} for next Friday"

    **Examples:**
    • "Apply SL for today" → Sick leave for today
    • "Apply EL for 25-09-2025" → Earned leave for Sep 25
    • "Apply CL for tomorrow" → Casual leave for tomorrow"""

            duration_days = len(leave_dates)
            print(f"✅ Final: {leave_type} for {duration_days} days on dates: {leave_dates}")
            
            # ========== VALIDATION CHECKS ==========
            
            # 1. Check EL minimum days requirement
            if leave_type == 'EL' and duration_days < 3:
                return f"""❌ **EL Minimum Duration Violation**

    Earned Leave requires exactly 3 consecutive working days.
    Your request: {duration_days} day{'s' if duration_days > 1 else ''}

    **Please apply for at least 3 consecutive days:**
    - "Apply EL for 3 days from {leave_dates[0].strftime('%d-%m-%Y')}"
    - "Apply EL from {leave_dates[0].strftime('%d-%m-%Y')} to {(leave_dates[0] + timedelta(days=2)).strftime('%d-%m-%Y')}" """

            # 2. Check CL maximum days requirement
            if leave_type == 'CL' and duration_days > 2:
                return f"""❌ **CL Maximum Duration Violation**

    Casual Leave allows maximum 2 consecutive days.
    Your request: {duration_days} days

    **Please apply for 1-2 days only.**"""

            # 3. Validate each date
            invalid_dates = []
            weekend_dates = []
            holiday_dates = []
            
            for leave_date in leave_dates:
                if db.is_weekend(leave_date):
                    weekend_dates.append(leave_date.strftime('%Y-%m-%d (%A)'))
                if db.is_public_holiday(leave_date):
                    holiday_dates.append(leave_date.strftime('%Y-%m-%d'))
            
            # Build validation messages
            validation_errors = []
            if weekend_dates:
                validation_errors.append(f"❌ **Weekend dates not allowed:** {', '.join(weekend_dates)}")
            if holiday_dates:
                validation_errors.append(f"❌ **Public holidays not allowed:** {', '.join(holiday_dates)}")
            
            if validation_errors:
                return "\n\n".join(validation_errors) + "\n\nPlease choose working days only."
            
            # 4. Check SL date restrictions (past dates and today only)
            if leave_type == 'SL':
                future_sl_dates = [date for date in leave_dates if date > today]
                if future_sl_dates:
                    future_dates_str = ', '.join([date.strftime('%Y-%m-%d') for date in future_sl_dates])
                    return f"""❌ **SL Date Restriction**

    Sick Leave cannot be applied for future dates.
    Future dates in your request: {future_dates_str}

    **Allowed:** Only past dates and today ({today.strftime('%Y-%m-%d')})"""
            
            # 5. Check date range restrictions for EL/CL
            if leave_type in ['EL', 'CL']:
                too_future_dates = [date for date in leave_dates if (date - today).days > 30]
                too_past_dates = [date for date in leave_dates if (today - date).days > 30]
                
                if too_future_dates:
                    future_dates_str = ', '.join([date.strftime('%Y-%m-%d') for date in too_future_dates])
                    return f"""❌ **Date Range Restriction**

    {leave_type} cannot be applied more than 30 days in advance.
    Future dates: {future_dates_str}

    **Allowed:** Within 30 days from today ({today.strftime('%Y-%m-%d')})"""
                
                if too_past_dates:
                    past_dates_str = ', '.join([date.strftime('%Y-%m-%d') for date in too_past_dates])
                    return f"""❌ **Date Range Restriction**

    {leave_type} cannot be applied for dates more than 30 days in the past.
    Past dates: {past_dates_str}

    **Allowed:** Within 30 days from today ({today.strftime('%Y-%m-%d')})"""
            
            # ========== APPLICATION PROCESSING ==========
            
            # Check balance
            balance = self.db.get_user_balance(user_id)
            print(f"✅ Balance check: {balance}")
            
            if not balance or balance[leave_type] < duration_days:
                return f"❌ Insufficient {leave_type} balance. Available: {balance[leave_type] if balance else 0} days, Required: {duration_days} days"
            
            # Simple reason detection
            reason = "Personal"
            if 'vacation' in message_lower:
                reason = "Vacation"
            elif any(word in message_lower for word in ['sick', 'fever', 'medical']):
                reason = "Medical"
            elif 'emergency' in message_lower:
                reason = "Emergency"
            elif any(word in message_lower for word in ['family', 'wedding']):
                reason = "Family function"
            
            # Submit applications
            successful_applications = 0
            application_dates = []
            
            for leave_date in leave_dates:
                # Format date for database
                leave_date_str = leave_date.strftime('%Y-%m-%d 00:00:00')
                print(f"🔍 Processing date: {leave_date_str}")
                
                # Check for date overlaps
                overlap = self.db.check_date_overlap(user_id, leave_date_str)
                print(f"✅ Overlap check for {leave_date_str}: {overlap}")
                
                if overlap:
                    return f"❌ Date conflict: You already have leave on {leave_date.strftime('%Y-%m-%d')}"
                
                # Add leave request to database
                print(f"💾 Adding to database: {leave_date_str}")
                success = self.db.add_leave_request(
                    user_id=user_id,
                    leave_date=leave_date_str,
                    leave_type=leave_type,
                    reason=reason,
                    duration="Full Day"
                )
                
                print(f"💾 Database result for {leave_date_str}: {success}")
                
                if success:
                    successful_applications += 1
                    application_dates.append(leave_date.strftime('%Y-%m-%d'))
                else:
                    return f"❌ Failed to submit application for {leave_date.strftime('%Y-%m-%d')}. The file might be locked. Please try again."
            
            if successful_applications > 0:
                date_range = application_dates[0]
                if len(application_dates) > 1:
                    date_range = f"{application_dates[0]} to {application_dates[-1]}"
                
                return f"""✅ **Leave Application Submitted Successfully!**

    📋 **Application Details:**
    • **Type:** {leave_type}
    • **Date:** {date_range} ({successful_applications} working days)
    • **Reason:** {reason}
    • **Status:** ⏳ Pending Approval
    • **Balance After Approval:** {balance[leave_type] - successful_applications} {leave_type} days

    Your manager will review your request."""
            else:
                return "❌ Failed to submit leave application."
                
        except Exception as e:
            print(f"❌ ERROR in _handle_leave_application: {str(e)}")
            import traceback
            traceback.print_exc()
            return "❌ Error processing your application. Please try again."

    def _extract_dates_improved(self, message, today):
        """Improved date extraction with better month name parsing"""
        leave_dates = []
        message_lower = message.lower()
        
        # Clean the message
        clean_message = message_lower
        remove_phrases = [
            'i want to apply', 'apply for', 'i need', 'want to take', 'take', 
            'leave', 'sl', 'el', 'cl', 'sick', 'earned', 'casual', 'medical',
            'apply', 'for', 'a', 'an', 'the'
        ]
        
        for phrase in remove_phrases:
            clean_message = clean_message.replace(phrase, ' ')
        
        clean_message = ' '.join(clean_message.split()).strip()
        print(f"🔍 Cleaned message: '{clean_message}'")
        
        # Handle month names like "sep25", "september25", "sep 25"
        month_patterns = {
            'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
            'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
            'aug': 8, 'august': 8, 'sep': 9, 'september': 9, 'oct': 10, 'october': 10,
            'nov': 11, 'november': 11, 'dec': 12, 'december': 12
        }
        
        # Try to find month patterns
        for month_name, month_num in month_patterns.items():
            if month_name in clean_message:
                # Extract day number
                day_match = re.search(r'(\d{1,2})', clean_message)
                if day_match:
                    day = int(day_match.group(1))
                    year = today.year
                    try:
                        parsed_date = datetime(year, month_num, day).date()
                        if parsed_date >= today:  # Only future dates for month names
                            leave_dates.append(parsed_date)
                            print(f"✅ Found month date: {month_name} {day} → {parsed_date}")
                            return leave_dates
                    except ValueError:
                        pass
        
        # Try specific date patterns (DD-MM-YYYY, DD/MM/YYYY, etc.)
        date_patterns = [
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',  # DD-MM-YYYY
            r'(\d{1,2})[-/](\d{1,2})',             # DD-MM (current year)
            r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',  # YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, clean_message)
            if matches:
                for match in matches:
                    try:
                        if len(match) == 3:  # DD-MM-YYYY or YYYY-MM-DD
                            if len(match[0]) == 4:  # YYYY-MM-DD
                                year, month, day = int(match[0]), int(match[1]), int(match[2])
                            else:  # DD-MM-YYYY
                                day, month, year = int(match[0]), int(match[1]), int(match[2])
                            leave_date = datetime(year, month, day).date()
                            leave_dates.append(leave_date)
                            print(f"✅ Found specific date: {leave_date}")
                        elif len(match) == 2:  # DD-MM (current year)
                            day, month = int(match[0]), int(match[1])
                            year = today.year
                            leave_date = datetime(year, month, day).date()
                            leave_dates.append(leave_date)
                            print(f"✅ Found date (current year): {leave_date}")
                        return leave_dates
                    except ValueError as e:
                        print(f"❌ Date parsing error: {e}")
                        continue
        
        # Handle natural language dates
        if 'today' in clean_message:
            leave_dates.append(today)
        elif 'yesterday' in clean_message:
            leave_dates.append(today - timedelta(days=1))
        elif 'tomorrow' in clean_message:
            leave_dates.append(today + timedelta(days=1))
        elif 'day after tomorrow' in clean_message:
            leave_dates.append(today + timedelta(days=2))
        
        # If still no dates found, try the original natural language parsing
        if not leave_dates:
            leave_dates = self._extract_dates_from_message(message)
        
        return leave_dates  
    
    def clear_chat_history_employee(user_id):
        """Clear chat history for employee from database"""
        if not user_id:
            return "Please login first!", []
        
        try:
            result = agent._clear_chat_history(user_id)
            # Return empty history after clearing
            return result, []
        except Exception as e:
            return f"Error clearing chat: {str(e)}", []

try:
    db = LeaveDatabase()
    auth = AuthSystem(db)
    agent = EnhancedLeaveChatbot(db)  # Use enhanced chatbot instead of SimpleLeaveAgent
    print("✅ All systems initialized successfully!")
    
except Exception as e:
    print(f"❌ System initialization failed: {e}")
    raise

def reset_database():
    """Reset the database with fresh sample data"""
    try:
        db = LeaveDatabase()
        print("✅ Database reset successfully!")
        return "Database reset successfully!"
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return f"Error resetting database: {e}"
# =============================================
# MAIN APPLICATION
# =============================================

with gr.Blocks(
    title="AI Leave Management System",
    css="""
    .gradio-container {
        max-width: 1200px !important;
    }
    .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        margin-bottom: 20px;
    }
    .login-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 40px;
        border-radius: 15px;
        color: white;
        margin-bottom: 30px;
        text-align: center;
    }
    .container-box {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
    }
    .admin-header {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        margin-bottom: 20px;
    }
    """
) as demo:
    
    # State variables
    current_user_state = gr.State("")
    user_role_state = gr.State("")
    
    # =============================================
    # LOGIN INTERFACE
    # =============================================
    
    with gr.Column(visible=True) as login_section:
        gr.Markdown("""
        <div class="login-header">
            <h1 style="margin: 0; font-size: 3em;">🏢 AI Leave Management System</h1>
            <p style="margin: 15px 0 0 0; font-size: 1.3em; opacity: 0.9;">Smart Leave Management with AI Assistant</p>
        </div>
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Column(elem_classes="container-box"):
                    gr.Markdown("### 🔐 Secure Login")
                    with gr.Row():
                        user_id_input = gr.Textbox(
                            label="User ID", 
                            placeholder="Enter your User ID",
                            scale=2
                        )
                        password_input = gr.Textbox(
                            label="Password", 
                            type="password", 
                            placeholder="Enter password",
                            value="leave",
                            scale=1
                        )
                    login_btn = gr.Button("🚀 Login to System", variant="primary", size="lg")
                    login_status = gr.Markdown("")
            
            with gr.Column(scale=1):
                with gr.Column(elem_classes="container-box"):
                    gr.Markdown("### 📋 System Information")
                    gr.Markdown("""
                    **🤖 AI Features:**
                    • Smart policy assistant
                    • Local rule-based system
                    • Real-time Excel updates
                    • Professional interface
                    
                    **🔑 Demo Credentials:**
                    - **Employees:** 1000-1010
                    - **Admins:** 5000, 8001, 6099  
                    - **Password:** `leave`
                    
                    **📊 Separate Interfaces:**
                    • 👤 Employee Portal
                    • 👨‍💼 Admin Dashboard
                    """)
    
    # =============================================
    # EMPLOYEE INTERFACE
    # =============================================
    
    with gr.Column(visible=False) as employee_section:
        # Header
        gr.Markdown("""
        <div class="dashboard-header">
            <h1 style="margin: 0; font-size: 2.5em;">👤 Employee Leave Portal</h1>
            <p style="margin: 10px 0 0 0; font-size: 1.2em; opacity: 0.9;">Manage your leaves and check balances</p>
        </div>
        """)
        
        with gr.Tab("💬 AI Leave Assistant"):
            with gr.Row():
                with gr.Column(scale=2):
                    chatbot_interface = gr.Chatbot(
                        label="AI Assistant Chat",
                        height=500,
                        show_copy_button=True,
                        container=True
                    )
                    with gr.Row():
                        chat_input = gr.Textbox(
                            show_label=False,
                            placeholder="Ask about policies, apply for leave, check balance...",
                            container=False,
                            scale=4
                        )
                        chat_submit = gr.Button("📤 Send", variant="primary", scale=1)
                
                with gr.Column(scale=1):
                    balance_display = gr.HTML()
                    gr.Markdown("### 🚀 Quick Actions")
                    with gr.Row():
                        quick_policy = gr.Button("📚 Ask Policy", size="sm", variant="secondary")
                        quick_balance = gr.Button("📊 Check Balance", size="sm", variant="secondary")
                    with gr.Row():
                        quick_status = gr.Button("📋 Application Status", size="sm", variant="secondary")
                        quick_help = gr.Button("❓ Get Help", size="sm", variant="secondary")
                    with gr.Row():
                        clear_chat_btn = gr.Button("🗑️ Clear Chat", size="sm", variant="stop")
                    
                    clear_chat_status = gr.Markdown("")
        
        with gr.Tab("📊 My Leave Applications"):
            gr.Markdown("### My Leave Applications")
            leave_requests_display = gr.HTML()
            with gr.Row():
                refresh_btn = gr.Button("🔄 Refresh Applications", variant="secondary")
        
        with gr.Tab("🔐 Logout"):
            gr.Markdown("### Logout")
            gr.Markdown("Click the button below to logout from the system.")
            logout_btn = gr.Button("🚪 Logout", variant="stop", size="lg")
            logout_status = gr.Markdown("")
    
    # =============================================
    # ADMIN INTERFACE
    # =============================================
    
    with gr.Column(visible=False) as admin_section:
        # Header
        gr.Markdown("""
        <div class="admin-header">
            <h1 style="margin: 0; font-size: 2.5em;">👨‍💼 Admin Leave Portal</h1>
            <p style="margin: 10px 0 0 0; font-size: 1.2em; opacity: 0.9;">Manage employee leave requests and approvals</p>
        </div>
        """)
        
        with gr.Tab("📋 Pending Approvals"):
            admin_status = gr.Markdown("### Loading pending requests...")
            pending_display = gr.Markdown()
            
            with gr.Row():
                approve_all_btn = gr.Button("✅ Approve All Requests", variant="primary", size="lg")
                refresh_admin_btn = gr.Button("🔄 Refresh List", variant="secondary")
            
            bulk_action_status = gr.Markdown("")
            
            gr.Markdown("### 🔧 Individual Actions")
            with gr.Row():
                with gr.Column(scale=1):
                    action_user_id = gr.Dropdown(
                        label="Select User",
                        choices=[],
                        interactive=True,
                        info="Select a user to see their pending dates"
                    )
                with gr.Column(scale=2):
                    action_leave_date = gr.Dropdown(
                        label="Select Leave Date", 
                        choices=[],
                        interactive=True,
                        info="Dates will appear after selecting a user"
                    )
            
            with gr.Row():
                individual_approve_btn = gr.Button("✅ Approve Selected", variant="primary")
                individual_reject_btn = gr.Button("❌ Reject Selected", variant="secondary")
            
            individual_status = gr.Markdown("")
        
        with gr.Tab("📈 System Analytics"):
            gr.Markdown("### System Overview")
            analytics_display = gr.HTML()
            refresh_analytics_btn = gr.Button("🔄 Refresh Analytics", variant="secondary")
        
        with gr.Tab("🔐 Logout"):
            gr.Markdown("### Logout")
            gr.Markdown("Click the button below to logout from the system.")
            admin_logout_btn = gr.Button("🚪 Logout", variant="stop", size="lg")
            admin_logout_status = gr.Markdown("")
            
    
    # =============================================
    # HELPER FUNCTIONS
    # =============================================
    
    def handle_login(user_id, password):
        """Handle user login"""
        if not user_id or not password:
            return (
                gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
                "❌ Please enter both User ID and Password", "", "", [], []
            )
        
        success, message = auth.authenticate(user_id, password)
        
        if success:
            current_user, role = auth.get_current_user()
            print(f"✅ Login successful: User={current_user}, Role={role}")  # Debug print
            
            # Get pending requests for dropdowns
            requests = db.get_pending_requests(current_user) if role == "admin" else []
            user_choices = list(set([str(req['UserId']) for req in requests]))
            date_choices = [req['Leave_Date'] for req in requests]
            
            if role == "employee":
                return (
                    gr.update(visible=False), gr.update(visible=True), gr.update(visible=False),
                    f"✅ {message}", current_user, role, user_choices, date_choices
                )
            else:  # admin
                return (
                    gr.update(visible=False), gr.update(visible=False), gr.update(visible=True),
                    f"✅ {message}", current_user, role, user_choices, date_choices
                )
        else:
            print(f"❌ Login failed: {message}")  # Debug print
            return (
                gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
                f"❌ {message}", "", "", [], []
            )
    
    def handle_logout():
        """Handle user logout"""
        auth.logout()
        return (
            gr.update(visible=True), gr.update(visible=False), gr.update(visible=False),
            "✅ Logged out successfully!", "", "", [], []
        )
    
    def chat_with_agent_employee(user_id, user_message, chat_history):
        """Handle chat with context-aware AI agent"""
        print(f"🔍 CHAT: user_id={user_id}, message='{user_message}'")
        
        if not user_id or user_id == "":
            return chat_history, "🔐 Please login first!"
        
        if not user_message or user_message.strip() == "":
            return chat_history, ""
        
        try:
            # Ensure chat_history is a list
            if chat_history is None:
                chat_history = []
                
            print(f"✅ Processing message for user: {user_id}")
            
            # Process message - make sure user_id is passed correctly
            bot_response = agent.process_message(str(user_id), user_message.strip())
            
            # Add to history in correct format
            new_history = chat_history + [[user_message, bot_response]]
            
            return new_history, ""
            
        except Exception as e:
            print(f"❌ Chat error: {e}")
            import traceback
            traceback.print_exc()
            error_msg = "I apologize, but I'm having trouble processing your request."
            new_history = chat_history + [[user_message, error_msg]]
            return new_history, ""

    def get_chat_history_employee(user_id):
        """Get chat history for display - ENSURES PROPER FORMAT"""
        if not user_id:
            return []
        try:
            history = agent.get_chat_history(user_id)
            print(f"✅ Loaded chat history: {len(history)} message pairs")
            
            # Ensure it's a list of lists
            if history and isinstance(history, list) and len(history) > 0:
                if isinstance(history[0], list) and len(history[0]) == 2:
                    return history
                else:
                    print(f"⚠️ History format issue, converting...")
                    # Convert to proper format
                    proper_history = []
                    for i, msg in enumerate(history):
                        if isinstance(msg, list) and len(msg) == 2:
                            proper_history.append(msg)
                        else:
                            # Skip invalid entries
                            continue
                    return proper_history
            return []
            
        except Exception as e:
            print(f"❌ Error loading chat history: {e}")
            return []

    def clear_chat_history_employee(user_id):
        """Clear chat history for employee - FIXED"""
        if not user_id:
            return "Please login first!", []
        
        try:
            # Clear from enhanced agent
            if hasattr(agent, 'clear_conversation_context'):
                agent.clear_conversation_context(user_id)
            
            # Clear from database
            result = agent._clear_chat_history(user_id)
            
            # Return empty history in proper format
            return "🗑️ Chat history cleared successfully!", []
            
        except Exception as e:
            print(f"❌ Error clearing chat: {e}")
            return f"Error clearing chat: {str(e)}", []
    
    def get_leave_balance_employee(user_id):
        """Get formatted leave balance for display"""
        if not user_id:
            return """
            <div style='text-align: center; padding: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white;'>
                <h3 style='margin: 0;'>🎯 Leave Balance</h3>
                <p style='margin: 10px 0 0 0;'>Please login to view your balance</p>
            </div>
            """
        
        balance = db.get_user_balance(user_id)
        if balance:
            return f"""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 15px; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.2);'>
                <h3 style='margin: 0 0 20px 0; text-align: center;'>🎯 Your Leave Balance</h3>
                <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 15px;'>
                    <div style='text-align: center; background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px; backdrop-filter: blur(10px);'>
                        <div style='font-size: 28px; font-weight: bold;'>{balance['EL']}</div>
                        <div style='font-size: 14px;'>🏖️ Earned Leave</div>
                    </div>
                    <div style='text-align: center; background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px; backdrop-filter: blur(10px);'>
                        <div style='font-size: 28px; font-weight: bold;'>{balance['SL']}</div>
                        <div style='font-size: 14px;'>🤒 Sick Leave</div>
                    </div>
                    <div style='text-align: center; background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px; backdrop-filter: blur(10px);'>
                        <div style='font-size: 28px; font-weight: bold;'>{balance['CL']}</div>
                        <div style='font-size: 14px;'>🎯 Casual Leave</div>
                    </div>
                    <div style='text-align: center; background: rgba(255,255,255,0.2); padding: 15px; border-radius: 10px; backdrop-filter: blur(10px);'>
                        <div style='font-size: 28px; font-weight: bold;'>{balance['TL']}</div>
                        <div style='font-size: 14px;'>📈 Total Available</div>
                    </div>
                </div>
            </div>
            """
        return """
        <div style='text-align: center; padding: 40px; background: #ff6b6b; border-radius: 15px; color: white;'>
            <h3 style='margin: 0;'>❌ Error</h3>
            <p style='margin: 10px 0 0 0;'>Could not load balance</p>
        </div>
        """
    
    def get_leave_requests_employee(user_id):
        """Get formatted leave requests for employee"""
        if not user_id:
            return "<p>Please login to view your applications</p>"
        
        requests = db.get_user_leave_requests(user_id)
        if not requests:
            return """
            <div style='text-align: center; padding: 40px; background: #f8f9fa; border-radius: 10px;'>
                <h3 style='color: #6c757d;'>📭 No Applications</h3>
                <p style='color: #6c757d;'>You haven't applied for any leaves yet.</p>
            </div>
            """
        
        html = """
        <div style='background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>
            <table style='width: 100%; border-collapse: collapse;'>
                <thead style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;'>
                    <tr>
                        <th style='padding: 15px; text-align: left;'>Date</th>
                        <th style='padding: 15px; text-align: left;'>Type</th>
                        <th style='padding: 15px; text-align: left;'>Reason</th>
                        <th style='padding: 15px; text-align: center;'>Status</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for req in requests[-10:]:
            # Fix datetime parsing safely
            leave_date = req['Leave_Date']
            if hasattr(leave_date, 'split'):
                date_str = leave_date.split()[0] if ' ' in str(leave_date) else str(leave_date)
            else:
                # Handle datetime objects
                date_str = str(leave_date).split()[0] if ' ' in str(leave_date) else str(leave_date)
            
            if req['Status'] == 'Approved':
                status_badge = "<span style='background: #28a745; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px;'>✅ Approved</span>"
            elif req['Status'] == 'Rejected':
                status_badge = "<span style='background: #dc3545; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px;'>❌ Rejected</span>"
            else:
                status_badge = "<span style='background: #ffc107; color: black; padding: 5px 10px; border-radius: 15px; font-size: 12px;'>⏳ Pending</span>"
            
            html += f"""
            <tr style='border-bottom: 1px solid #eee;'>
                <td style='padding: 15px;'>{date_str}</td>
                <td style='padding: 15px;'>{req['LeaveType']}</td>
                <td style='padding: 15px;'>{req['Reason']}</td>
                <td style='padding: 15px; text-align: center;'>{status_badge}</td>
            </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
        return html
    
    
    def get_pending_display_admin(admin_id):
        """Get pending requests for admin - FIXED"""
        if not admin_id:
            return "Please login as admin", "Please login to view pending requests"
        
        try:
            requests = db.get_pending_requests(admin_id)
            
            if not requests:
                return "### 📋 Pending Approvals", "**No pending leave requests found.**\n\nIf you just created leave applications, make sure they are assigned to your admin ID."
            
            # Simple text display
            display_text = f"**Pending Leave Requests: {len(requests)}**\n\n"
            
            for i, req in enumerate(requests, 1):
                # Safe date formatting
                leave_date = str(req['Leave_Date']).split()[0]
                applied_date = str(req['AppliedDate']).split()[0]
                
                display_text += f"**Request {i}:**\n"
                display_text += f"• **User:** {req['UserId']}\n"
                display_text += f"• **Date:** {leave_date}\n"
                display_text += f"• **Type:** {req['LeaveType']}\n"
                display_text += f"• **Reason:** {req['Reason']}\n"
                display_text += f"• **Applied:** {applied_date}\n\n"
            
            return "### 📋 Pending Approvals", display_text
            
        except Exception as e:
            return "### ❌ Error", f"Error loading requests: {str(e)}"
    
    def update_user_dropdown(admin_id):
        """Update user dropdown choices"""
        if not admin_id:
            return []
        
        try:
            requests = db.get_pending_requests(admin_id)
            user_choices = list(set([str(req['UserId']) for req in requests]))
            print(f"✅ User dropdown updated: {user_choices}")
            return user_choices
        except Exception as e:
            print(f"❌ Error updating user dropdown: {e}")
            return []

    def update_date_dropdown(admin_id, selected_user):
        """Update date dropdown based on selected user - FIXED"""
        if not admin_id or not selected_user:
            return gr.update(choices=[])
        
        try:
            print(f"🔍 Updating dates for user: {selected_user} (type: {type(selected_user)})")
            
            requests = db.get_pending_requests(admin_id)
            
            # Filter dates for the selected user only
            date_choices = []
            for req in requests:
                # Convert both to string for comparison
                if str(req['UserId']) == str(selected_user):
                    # Format the date nicely
                    leave_date = req['Leave_Date']
                    if hasattr(leave_date, 'split'):
                        formatted_date = leave_date.split()[0] if ' ' in str(leave_date) else str(leave_date)
                    else:
                        formatted_date = str(leave_date).split()[0] if ' ' in str(leave_date) else str(leave_date)
                    
                    date_choices.append(req['Leave_Date'])  # Keep original for database operations
            
            print(f"✅ Date choices for user {selected_user}: {len(date_choices)} dates")
            return gr.update(choices=date_choices)
            
        except Exception as e:
            print(f"❌ Error updating date dropdown: {e}")
            return gr.update(choices=[])

    def update_admin_dropdowns(admin_id):
        """Update both dropdowns - FIXED TYPE HANDLING"""
        if not admin_id:
            return gr.update(choices=[]), gr.update(choices=[])
        
        try:
            requests = db.get_pending_requests(admin_id)
            print(f"🔍 Found {len(requests)} pending requests for admin {admin_id}")
            
            if not requests:
                return gr.update(choices=[]), gr.update(choices=[])
            
            # Convert user IDs to strings for dropdown compatibility
            user_choices = [str(req['UserId']) for req in requests]
            user_choices = list(set(user_choices))  # Remove duplicates
            user_choices.sort()  # Sort for better UX
            
            print(f"✅ User choices: {user_choices}")
            
            # For initial load, return empty dates (will be populated when user is selected)
            return gr.update(choices=user_choices), gr.update(choices=[])
            
        except Exception as e:
            print(f"❌ Error updating dropdowns: {e}")
            return gr.update(choices=[]), gr.update(choices=[])
    
    def handle_individual_approve(admin_id, user_id, leave_date):
        """Handle individual approval - IMPROVED"""
        print(f"🔍 APPROVE: admin={admin_id}, user={user_id}, date={leave_date}")
        
        if not admin_id:
            return "❌ Please login as admin", gr.update(), gr.update(), gr.update(), gr.update()
        
        if not user_id:
            return "❌ Please select a user", gr.update(), gr.update(), gr.update(), gr.update()
        
        if not leave_date:
            return "❌ Please select a date", gr.update(), gr.update(), gr.update(), gr.update()
        
        try:
            success = db.update_leave_status(user_id, leave_date, "Approved")
            if success:
                result = f"✅ Approved leave for User {user_id} on {leave_date.split()[0]}"
            else:
                result = f"❌ Failed to approve leave for User {user_id}"
            
            # Refresh everything
            display, status = get_pending_display_admin(admin_id)
            user_choices = update_user_dropdown(admin_id)
            
            return result, display, status, gr.update(choices=user_choices), gr.update(choices=[])
            
        except Exception as e:
            print(f"❌ Error in individual approve: {str(e)}")
            return f"❌ Error: {str(e)}", gr.update(), gr.update(), gr.update(), gr.update()

    def handle_individual_reject(admin_id, user_id, leave_date):
        """Handle individual rejection - IMPROVED"""
        print(f"🔍 REJECT: admin={admin_id}, user={user_id}, date={leave_date}")
        
        if not admin_id:
            return "❌ Please login as admin", gr.update(), gr.update(), gr.update(), gr.update()
        
        if not user_id:
            return "❌ Please select a user", gr.update(), gr.update(), gr.update(), gr.update()
        
        if not leave_date:
            return "❌ Please select a date", gr.update(), gr.update(), gr.update(), gr.update()
        
        try:
            success = db.update_leave_status(user_id, leave_date, "Rejected")
            if success:
                result = f"❌ Rejected leave for User {user_id} on {leave_date.split()[0]}"
            else:
                result = f"❌ Failed to reject leave for User {user_id}"
            
            # Refresh everything
            display, status = get_pending_display_admin(admin_id)
            user_choices = update_user_dropdown(admin_id)
            
            return result, display, status, gr.update(choices=user_choices), gr.update(choices=[])
            
        except Exception as e:
            print(f"❌ Error in individual reject: {str(e)}")
            return f"❌ Error: {str(e)}", gr.update(), gr.update(), gr.update(), gr.update()
    
    def handle_approve_all(admin_id):
        """Handle approve all requests - FIXED VERSION"""
        print(f"🔍 APPROVE ALL: admin={admin_id}")
        
        if not admin_id:
            return "❌ Please login as admin", gr.update(), gr.update(), gr.update(), gr.update()
        
        try:
            approved_count, total_count = db.approve_all_pending(admin_id)
            
            if approved_count > 0:
                result = f"✅ Successfully approved {approved_count} out of {total_count} requests!"
            else:
                result = f"❌ No requests were approved. Please check if there are pending requests."
            
            # Refresh the display
            display, status = get_pending_display_admin(admin_id)
            user_choices, date_choices = update_admin_dropdowns(admin_id)
            
            return result, display, status, gr.update(choices=user_choices), gr.update(choices=date_choices)
            
        except Exception as e:
            print(f"❌ Error in approve all: {str(e)}")
            error_msg = f"❌ Error approving all requests: {str(e)}"
            return error_msg, gr.update(), gr.update(), gr.update(), gr.update()
    
    def get_analytics_admin():
        """Get system analytics for admin"""
        try:
            # Read data from Excel
            df_available = pd.read_excel(Config.EXCEL_FILE, sheet_name='Available')
            df_hierarchy = pd.read_excel(Config.EXCEL_FILE, sheet_name='Hierarchy')
            
            # Calculate stats
            total_employees = len(df_available)
            total_pending = len(df_hierarchy[df_hierarchy['Status'] == 'Pending'])
            total_approved = len(df_hierarchy[df_hierarchy['Status'] == 'Approved'])
            total_rejected = len(df_hierarchy[df_hierarchy['Status'] == 'Rejected'])
            
            html = f"""
            <div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-bottom: 30px;'>
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 15px; color: white; text-align: center;'>
                    <div style='font-size: 32px; font-weight: bold;'>{total_employees}</div>
                    <div style='font-size: 16px;'>👥 Total Employees</div>
                </div>
                <div style='background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); padding: 25px; border-radius: 15px; color: white; text-align: center;'>
                    <div style='font-size: 32px; font-weight: bold;'>{total_pending}</div>
                    <div style='font-size: 16px;'>⏳ Pending Requests</div>
                </div>
                <div style='background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 25px; border-radius: 15px; color: white; text-align: center;'>
                    <div style='font-size: 32px; font-weight: bold;'>{total_approved}</div>
                    <div style='font-size: 16px;'>✅ Approved Requests</div>
                </div>
                <div style='background: linear-gradient(135deg, #6c757d 0%, #495057 100%); padding: 25px; border-radius: 15px; color: white; text-align: center;'>
                    <div style='font-size: 32px; font-weight: bold;'>{total_rejected}</div>
                    <div style='font-size: 16px;'>❌ Rejected Requests</div>
                </div>
            </div>
            
            <div style='background: white; padding: 25px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);'>
                <h3 style='margin-top: 0;'>📊 Recent System Activity</h3>
                <p>System is running smoothly with {total_employees} employees registered.</p>
                <p>Current pending requests: <strong>{total_pending}</strong></p>
            </div>
            """
            
            return html
            
        except Exception as e:
            return f"<p>❌ Error loading analytics: {str(e)}</p>"
        
    def clear_pending_requests():
        """Clear all pending requests from the database"""
        try:
            db = LeaveDatabase()
            df_hierarchy = pd.read_excel(db.file_path, sheet_name='Hierarchy')
            
            # Remove all pending requests
            df_hierarchy = df_hierarchy[df_hierarchy['Status'] != 'Pending']
            
            # Save back to Excel
            with pd.ExcelWriter(db.file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df_hierarchy.to_excel(writer, sheet_name='Hierarchy', index=False)
            
            print("✅ All pending requests cleared!")
            return "All pending requests cleared. New applications will have current dates."
        except Exception as e:
            print(f"❌ Error clearing pending requests: {e}")
            return f"Error: {e}"
    
    def reset_admin_dropdowns():
        """Reset admin dropdowns to empty state"""
        return gr.update(choices=[]), gr.update(choices=[])
    
    # =============================================
    # EVENT HANDLERS
    # =============================================
    
    # Login handlers
    login_btn.click(
        fn=handle_login,
        inputs=[user_id_input, password_input],
        outputs=[login_section, employee_section, admin_section, login_status, current_user_state, user_role_state, action_user_id, action_leave_date]
    ).then(
        fn=lambda uid: get_pending_display_admin(uid),
        inputs=[current_user_state],
        outputs=[pending_display, admin_status]
    ).then(
        fn=lambda uid: update_admin_dropdowns(uid),
        inputs=[current_user_state],
        outputs=[action_user_id, action_leave_date]
    ).then(
        fn=lambda uid: get_leave_balance_employee(uid),  # ADD THIS LINE
        inputs=[current_user_state],
        outputs=[balance_display]
    ).then(
        fn=lambda uid: get_leave_requests_employee(uid),  # ADD THIS LINE
        inputs=[current_user_state],
        outputs=[leave_requests_display]
    ).then(
        fn=lambda uid: get_chat_history_employee(uid),  # ADD THIS LINE
        inputs=[current_user_state],
        outputs=[chatbot_interface]
    )
    
    # Employee interface handlers
    chat_submit.click(
        fn=chat_with_agent_employee,
        inputs=[current_user_state, chat_input, chatbot_interface],
        outputs=[chatbot_interface, chat_input]
    ).then(
        fn=lambda uid: get_leave_balance_employee(uid),
        inputs=[current_user_state],
        outputs=[balance_display]
    )
    
    chat_input.submit(
        fn=chat_with_agent_employee,
        inputs=[current_user_state, chat_input, chatbot_interface],
        outputs=[chatbot_interface, chat_input]
    ).then(
        fn=lambda uid: get_leave_balance_employee(uid),
        inputs=[current_user_state],
        outputs=[balance_display]
    )
    
    # Quick action buttons
        # Quick action buttons
    quick_policy.click(
        fn=lambda uid: chat_with_agent_employee(uid, "What are the leave policies?", get_chat_history_employee(uid)),
        inputs=[current_user_state],
        outputs=[chatbot_interface, chat_input]
    ).then(
        fn=lambda uid: get_leave_balance_employee(uid),
        inputs=[current_user_state],
        outputs=[balance_display]
    )
    
    quick_balance.click(
        fn=lambda uid: chat_with_agent_employee(uid, "What is my leave balance?", get_chat_history_employee(uid)),
        inputs=[current_user_state],
        outputs=[chatbot_interface, chat_input]
    ).then(
        fn=lambda uid: get_leave_balance_employee(uid),
        inputs=[current_user_state],
        outputs=[balance_display]
    )
    
    quick_status.click(
        fn=lambda uid: chat_with_agent_employee(uid, "What is my application status?", get_chat_history_employee(uid)),
        inputs=[current_user_state],
        outputs=[chatbot_interface, chat_input]
    )
    
    quick_help.click(
        fn=lambda uid: chat_with_agent_employee(uid, "What can you help me with?", get_chat_history_employee(uid)),
        inputs=[current_user_state],
        outputs=[chatbot_interface, chat_input]
    )
    
    clear_chat_btn.click(
        fn=clear_chat_history_employee,
        inputs=[current_user_state],
        outputs=[clear_chat_status, chatbot_interface]
    )
    
    refresh_btn.click(
        fn=get_leave_requests_employee,
        inputs=[current_user_state],
        outputs=[leave_requests_display]
    )
    
    logout_btn.click(
        fn=handle_logout,
        outputs=[login_section, employee_section, admin_section, logout_status, current_user_state, user_role_state, action_user_id, action_leave_date]
    ).then(
        fn=reset_admin_dropdowns,
        outputs=[action_user_id, action_leave_date]
    )
    
    # Admin interface handlers
    refresh_admin_btn.click(
        fn=lambda uid: get_pending_display_admin(uid),
        inputs=[current_user_state],
        outputs=[admin_status, pending_display]
    ).then(
        fn=lambda uid: update_admin_dropdowns(uid),
        inputs=[current_user_state],
        outputs=[action_user_id, action_leave_date]
    )
    
    # When user selection changes, update date dropdown
    action_user_id.change(
        fn=lambda uid, user: update_date_dropdown(uid, user),
        inputs=[current_user_state, action_user_id],
        outputs=[action_leave_date]
    )
    
    approve_all_btn.click(
        fn=lambda uid: handle_approve_all(uid),
        inputs=[current_user_state],
        outputs=[bulk_action_status, pending_display, admin_status, action_user_id, action_leave_date]
    )
    
    individual_approve_btn.click(
        fn=lambda uid, user_id, date: handle_individual_approve(uid, user_id, date),
        inputs=[current_user_state, action_user_id, action_leave_date],
        outputs=[individual_status, pending_display, admin_status, action_user_id, action_leave_date]
    )
    
    individual_reject_btn.click(
        fn=lambda uid, user_id, date: handle_individual_reject(uid, user_id, date),
        inputs=[current_user_state, action_user_id, action_leave_date],
        outputs=[individual_status, pending_display, admin_status, action_user_id, action_leave_date]
    )
    
    refresh_analytics_btn.click(
        fn=get_analytics_admin,
        outputs=[analytics_display]
    )
    
    admin_logout_btn.click(
        fn=handle_logout,
        outputs=[login_section, employee_section, admin_section, admin_logout_status, current_user_state, user_role_state, action_user_id, action_leave_date]
    ).then(
        fn=reset_admin_dropdowns,
        outputs=[action_user_id, action_leave_date]
    )
    
    # Initial loads
    demo.load(
        fn=lambda uid: get_leave_balance_employee(uid),
        inputs=[current_user_state],
        outputs=[balance_display]
    ).then(
        fn=lambda uid: get_leave_requests_employee(uid),
        inputs=[current_user_state],
        outputs=[leave_requests_display]
    ).then(
        fn=lambda uid: get_chat_history_employee(uid),
        inputs=[current_user_state],
        outputs=[chatbot_interface]
    )


# =============================================
# LAUNCH APPLICATION
# =============================================

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("🚀 AI Leave Management System - Starting Server...")
    print(f"{'='*60}")
    print("📊 Features:")
    print("  • Smart Policy Assistant")
    print("  • Local Rule-Based System")
    print("  • Real-time Excel Updates")
    print("  • Separate Employee & Admin Interfaces")
    print("")
    print("🔑 Demo Credentials:")
    print("  Employees: 1000-1010 | Admins: 5000, 8001, 6099")
    print("  Password: leave")
    print("")
    print(f"🌐 Server starting at: http://{Config.HOST}:{Config.PORT}")
    print(f"{'='*60}")
    
    try:
        demo.launch(
            server_name=Config.HOST,
            server_port=Config.PORT,
            share=False,
            show_error=True
        )
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("💡 Try these solutions:")
        print("  1. Check if port 7860 is available")
        print("  2. Try changing PORT to 7861 in config.py")
        print("  3. Make sure no other Gradio app is running")
        
    def debug_dropdowns(admin_id):
        """Debug dropdown states"""
        if not admin_id:
            return "No admin ID"
        
        requests = db.get_pending_requests(admin_id)
        user_choices = list(set([str(req['UserId']) for req in requests]))
        
        debug_info = f"""
        **Debug Info:**
        - Admin ID: {admin_id}
        - Total pending requests: {len(requests)}
        - Unique users: {user_choices}
        """
        
        for user in user_choices:
            user_dates = [req['Leave_Date'] for req in requests if str(req['UserId']) == user]
            debug_info += f"\n- User {user}: {len(user_dates)} dates"
        
        return debug_info
    
