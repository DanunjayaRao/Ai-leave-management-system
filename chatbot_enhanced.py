import re
import pandas as pd
from datetime import datetime, timedelta
from dateparser import parse as date_parse
import os

class EnhancedLeaveChatbot:
    def __init__(self, database):
        self.db = database
        self.conversation_context = {}
        
    def process_message(self, user_id, message):
        """Process user message with clear step-by-step conversation flow"""
        print(f"🔍 CHAT PROCESSING: user_id={user_id}, message='{message}'")
        
        try:
            if not user_id:
                return "🔐 Please login first to use the chatbot."
                
            if not message or str(message).strip() == "":
                return "Please provide a valid message."
            
            # Initialize or get user context
            if user_id not in self.conversation_context:
                self.conversation_context[user_id] = {
                    'current_flow': None,  # 'leave_application'
                    'current_step': 0,     # 0=idle, 1=asked_type, 2=asked_dates
                    'pending_leave_type': None,
                    'pending_dates': None,
                    'conversation_history': []
                }
            
            context = self.conversation_context[user_id]
            user_message = str(message).strip()
            
            # Save user message
            self.db.save_chat_message(user_id, 'user', user_message)
            
            # Generate response based on current flow state
            response = self._handle_conversation_flow(user_id, user_message, context)
            
            # Save bot response
            self.db.save_chat_message(user_id, 'assistant', response)
            
            return response
            
        except Exception as e:
            print(f"❌ Error in process_message: {e}")
            import traceback
            traceback.print_exc()
            return "I apologize, but I'm having trouble processing your request right now. Please try again."

    def _handle_conversation_flow(self, user_id, message, context):
        """Handle the step-by-step conversation flow"""
        message_lower = message.lower()
        
        print(f"🎯 Current flow: {context['current_flow']}, step: {context['current_step']}")
        
        # Step 0: No active flow - detect if user wants to apply leave
        if context['current_flow'] is None:
            if any(word in message_lower for word in ['apply', 'want', 'need', 'request', 'would like']) and 'leave' in message_lower:
                return self._start_leave_application(message, context)
            else:
                return self._handle_other_requests(user_id, message)
        
        # Step 1: We've asked for leave type, waiting for response
        elif context['current_flow'] == 'leave_application' and context['current_step'] == 1:
            leave_type = self._extract_leave_type(message_lower)
            if leave_type:
                context['pending_leave_type'] = leave_type
                context['current_step'] = 2  # Move to date step
                return self._ask_for_dates(leave_type)
            else:
                return self._ask_leave_type_again()
        
        # Step 2: We've asked for dates, waiting for response
        elif context['current_flow'] == 'leave_application' and context['current_step'] == 2:
            dates = self._extract_dates_advanced(message)
            if dates:
                context['pending_dates'] = dates
                # Process the complete application
                return self._process_leave_application(user_id, context)
            else:
                return self._ask_for_dates_again(context['pending_leave_type'])
        
        else:
            # Reset if something unexpected happens
            self._reset_flow(context)
            return "I lost track of our conversation. How can I help you?"

    def _start_leave_application(self, message, context):
        """Start a new leave application flow"""
        print("🚀 Starting leave application flow")
        
        # Extract any leave type mentioned in initial message
        leave_type = self._extract_leave_type(message.lower())
        dates = self._extract_dates_advanced(message)
        
        context['current_flow'] = 'leave_application'
        
        if leave_type and dates:
            # User provided both type and dates in one message
            context['pending_leave_type'] = leave_type
            context['pending_dates'] = dates
            context['current_step'] = 2
            # We'll process this in the main flow
            return "I see you want to apply for leave. Let me process your request..."
        elif leave_type:
            # User provided only type
            context['pending_leave_type'] = leave_type
            context['current_step'] = 2
            return self._ask_for_dates(leave_type)
        else:
            # User didn't specify type
            context['current_step'] = 1
            return self._ask_leave_type()

    def _ask_leave_type(self):
        """Ask for leave type - Step 1"""
        return """🏖️ **What type of leave? (EL/SL/CL)**

Please specify:
• **EL** - Earned Leave (min 3 days, for vacations)
• **SL** - Sick Leave (today/past dates, for medical)  
• **CL** - Casual Leave (max 2 days, for emergencies)

You can just type: **EL**, **SL**, or **CL**"""

    def _ask_leave_type_again(self):
        """Ask for leave type again if not understood"""
        return """❓ **I didn't catch the leave type.**

Please specify: **EL**, **SL**, or **CL**

• EL - Earned Leave (min 3 days)
• SL - Sick Leave (today/past dates)  
• CL - Casual Leave (max 2 days)"""

    def _ask_for_dates(self, leave_type):
        """Ask for dates - Step 2"""
        return f"""📅 **When for {leave_type}? (dates)**

Please specify the date(s):
• "today" or "tomorrow"
• "25Sep2024" or "25-09-2024"
• "25Sep2024 to 27Sep2024"
• "from Friday to Monday"

**Today:** {datetime.now().strftime('%d-%b-%Y')}"""

    def _ask_for_dates_again(self, leave_type):
        """Ask for dates again if not understood"""
        return f"""❓ **I need the dates for your {leave_type}.**

Please specify when:
• "today" or "tomorrow"
• "25Sep2024" or "25-09-2024" 
• "from Friday to Monday"
• "25Sep2024 to 27Sep2024"

**Today:** {datetime.now().strftime('%d-%b-%Y')}"""

    def _process_leave_application(self, user_id, context):
        """Process the complete leave application and reset flow"""
        leave_type = context['pending_leave_type']
        dates = context['pending_dates']
        
        print(f"✅ Processing {leave_type} application for dates: {dates}")
        
        # Reset flow first
        self._reset_flow(context)
        
        # Validate dates
        today = datetime.now().date()
        validation_errors = []
        
        for date in dates:
            # Check SL restrictions
            if leave_type == 'SL' and date > today:
                validation_errors.append(f"❌ SL cannot be applied for future dates: {date.strftime('%d-%b-%Y')}")
            
            # Check weekends
            if self.db.is_weekend(date):
                validation_errors.append(f"❌ Cannot apply leave on weekends: {date.strftime('%d-%b-%Y')} ({date.strftime('%A')})")
        
        # Check EL minimum days
        if leave_type == 'EL' and len(dates) < 3:
            validation_errors.append("❌ EL requires minimum 3 consecutive days")
        
        # Check CL maximum days  
        if leave_type == 'CL' and len(dates) > 2:
            validation_errors.append("❌ CL allows maximum 2 consecutive days")
        
        if validation_errors:
            return "\n".join(validation_errors) + "\n\nPlease start over with 'Apply for leave'."
        
        # Check balance
        balance = self.db.get_user_balance(user_id)
        if not balance:
            return "❌ Unable to check your leave balance. Please try 'Apply for leave' again."
            
        if balance[leave_type] < len(dates):
            return f"❌ Insufficient {leave_type} balance. Available: {balance[leave_type]} days, Required: {len(dates)} days\n\nPlease start over with 'Apply for leave'."
        
        # Submit applications
        successful_applications = 0
        for leave_date in dates:
            leave_date_str = leave_date.strftime('%Y-%m-%d 00:00:00')
            
            # Check for date conflicts
            if self.db.check_date_overlap(user_id, leave_date_str):
                return f"❌ Date conflict: You already have leave on {leave_date.strftime('%d-%b-%Y')}\n\nPlease start over with 'Apply for leave'."
            
            # Add leave request
            success = self.db.add_leave_request(
                user_id=user_id,
                leave_date=leave_date_str,
                leave_type=leave_type,
                reason="Personal",
                duration="Full Day"
            )
            
            if success:
                successful_applications += 1
        
        if successful_applications > 0:
            date_range = dates[0].strftime('%d-%b-%Y')
            if len(dates) > 1:
                date_range = f"{dates[0].strftime('%d-%b-%Y')} to {dates[-1].strftime('%d-%b-%Y')}"
            
            return f"""✅ **Application Submitted!**

📋 **Details:**
• **Type:** {leave_type}
• **Date:** {date_range} ({successful_applications} day{'s' if successful_applications > 1 else ''})
• **Status:** ⏳ Pending Approval
• **Balance After:** {balance[leave_type] - successful_applications} {leave_type} days

Your manager will review your request."""
        
        return "❌ Failed to submit application. Please try 'Apply for leave' again."

    def _handle_other_requests(self, user_id, message):
        """Handle non-leave-application requests"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['balance', 'remaining']):
            return self._get_balance_response(user_id)
        elif any(word in message_lower for word in ['status', 'pending']):
            return self._get_status_response(user_id)
        elif any(word in message_lower for word in ['policy', 'rule']):
            return self._get_policy_response()
        elif any(word in message_lower for word in ['hello', 'hi', 'hey']):
            return self._get_greeting_response(user_id)
        elif any(word in message_lower for word in ['help']):
            return self._get_help_response()
        else:
            return self._handle_general_query(message)

    def _reset_flow(self, context):
        """Reset the conversation flow"""
        context['current_flow'] = None
        context['current_step'] = 0
        context['pending_leave_type'] = None
        context['pending_dates'] = None

    def _extract_leave_type(self, message):
        """Extract leave type from message"""
        if any(word in message for word in ['el', 'earned']):
            return 'EL'
        elif any(word in message for word in ['sl', 'sick']):
            return 'SL'
        elif any(word in message for word in ['cl', 'casual']):
            return 'CL'
        return None

    def _extract_dates_advanced(self, message):
        """Extract dates from natural language"""
        dates = []
        today = datetime.now().date()
        
        print(f"🔍 Extracting dates from: '{message}'")
        
        # Handle date ranges with "to" or "until"
        range_pattern = r'(\d{1,2}[-\/]?\w+[-\/]?\d{0,4})\s*(?:to|until|til|-)\s*(\d{1,2}[-\/]?\w+[-\/]?\d{0,4})'
        range_match = re.search(range_pattern, message, re.IGNORECASE)
        
        if range_match:
            start_str, end_str = range_match.groups()
            start_date = self._parse_single_date(start_str)
            end_date = self._parse_single_date(end_str)
            
            if start_date and end_date and start_date <= end_date:
                current = start_date
                while current <= end_date:
                    if not self.db.is_weekend(current):
                        dates.append(current)
                    current += timedelta(days=1)
                print(f"✅ Found date range: {start_date} to {end_date} -> {len(dates)} dates")
                return dates
        
        # Handle single dates
        single_date = self._parse_single_date(message)
        if single_date:
            dates.append(single_date)
            print(f"✅ Found single date: {single_date}")
        
        return dates

    def _parse_single_date(self, date_str):
        """Parse a single date from various formats"""
        today = datetime.now().date()
        
        # Natural language dates
        natural_dates = {
            'today': today,
            'tomorrow': today + timedelta(days=1),
            'yesterday': today - timedelta(days=1),
        }
        
        for key, date_val in natural_dates.items():
            if key in date_str.lower():
                return date_val
        
        # Try different date formats
        date_formats = [
            '%d-%b-%Y', '%d-%m-%Y', '%d/%m/%Y', '%d %b %Y',
            '%d-%b', '%d-%m', '%d/%m', '%b %d', '%d %b'
        ]
        
        for fmt in date_formats:
            try:
                # Clean the date string
                clean_str = re.sub(r'[^\w\s-]', '', date_str.strip())
                parsed_date = datetime.strptime(clean_str, fmt)
                
                # If year not specified, use current year
                if parsed_date.year == 1900:
                    parsed_date = parsed_date.replace(year=today.year)
                
                return parsed_date.date()
            except ValueError:
                continue
        
        # Try dateparser as fallback
        try:
            parsed = date_parse(date_str)
            if parsed:
                return parsed.date()
        except:
            pass
        
        return None

    def _get_balance_response(self, user_id):
        """Get balance response"""
        balance = self.db.get_user_balance(user_id)
        if balance:
            return f"""📊 **Your Leave Balance:**

• EL: {balance['EL']} days (min 3 days)
• SL: {balance['SL']} days (today/past dates)  
• CL: {balance['CL']} days (max 2 days)
• Total: {balance['TL']} days

**Today:** {datetime.now().strftime('%d-%b-%Y')}"""
        return "❌ Unable to fetch your leave balance."

    def _get_status_response(self, user_id):
        """Get status response"""
        requests = self.db.get_user_leave_requests(user_id)
        if requests:
            response = "📋 **Your Applications:**\n\n"
            for req in reversed(requests[-5:]):
                status_icon = "✅" if req['Status'] == 'Approved' else "❌" if req['Status'] == 'Rejected' else "⏳"
                date_str = req['Leave_Date'].split()[0] if ' ' in str(req['Leave_Date']) else str(req['Leave_Date'])
                response += f"{status_icon} {date_str} - {req['LeaveType']} - {req['Status']}\n"
            return response
        return "📋 No applications found."

    def _get_policy_response(self):
        """Get policy response"""
        return f"""📚 **Leave Policies:**

• EL: Min 3 days, ±30 days
• SL: Today/past dates only, max 15 days before  
• CL: Max 2 days, ±30 days

**Today:** {datetime.now().strftime('%d-%b-%Y')}"""

    def _get_greeting_response(self, user_id):
        """Get greeting response"""
        balance = self.db.get_user_balance(user_id)
        if balance:
            return f"""👋 **Hello! I'm your AI Leave Assistant**

I can help you:
• Apply for leave (step-by-step guidance)
• Check your balance
• View application status

**Try:** "Apply for leave" to get started!"""
        return "👋 Hello! How can I help you with leave management?"

    def _get_help_response(self):
        """Get help response"""
        return """🤖 **How to apply for leave:**

1. Say: "Apply for leave" or "I want to apply leave"
2. I'll ask: "What type of leave? (EL/SL/CL)"
3. You specify: "EL", "SL", or "CL"  
4. I'll ask: "When? (dates)"
5. You provide dates: "25Sep2024" or "today" or "25Sep2024 to 27Sep2024"
6. I'll submit your application!

**Other commands:**
"Check balance", "Application status", "Leave policies\""""

    def _handle_general_query(self, message):
        """Handle general queries"""
        return f"""🤔 I understand you're asking about: "{message}"

I specialize in leave management. Here's what I can help with:

• **Apply for leave** (I'll guide you step by step)
• Check your leave balance
• View application status  
• Explain leave policies

**To apply for leave, just say:** "Apply for leave"

I'll walk you through the process step by step!"""

    def get_chat_history(self, user_id):
        """Get chat history in Gradio format"""
        try:
            chat_records = self.db.get_chat_history(user_id)
            gradio_history = []
            current_user_msg = None
            
            for record in chat_records:
                if record['Role'] == 'user':
                    current_user_msg = record['Message']
                elif record['Role'] == 'assistant' and current_user_msg is not None:
                    gradio_history.append([current_user_msg, record['Message']])
                    current_user_msg = None
            
            return gradio_history
            
        except Exception as e:
            print(f"❌ Error getting chat history: {e}")
            return []

    def clear_conversation_context(self, user_id):
        """Clear conversation context"""
        if user_id in self.conversation_context:
            self.conversation_context[user_id] = {
                'current_flow': None,
                'current_step': 0,
                'pending_leave_type': None,
                'pending_dates': None,
                'conversation_history': []
            }
        self.db.clear_chat_history(user_id)