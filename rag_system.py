import os
import pandas as pd
from datetime import datetime, timedelta
import dateparser
import PyPDF2
import re
from config import Config

class LeavePolicyRAG:
    def __init__(self, database):
        self.db = database
        self.policy_knowledge = self._load_policy_from_pdf()
        self.contact_info = self._load_contact_info()
        print("✅ Policy system initialized with PDF rules")
    
    def _load_policy_from_pdf(self):
        """Load policy rules from PDF file"""
        try:
            pdf_path = Config.PDF_FILE
            print(f"📖 Attempting to load PDF from: {pdf_path}")
            
            if not os.path.exists(pdf_path):
                print(f"⚠️ PDF file not found: {pdf_path}. Using default rules.")
                return self._get_default_rules()
            
            policy_text = self._extract_text_from_pdf(pdf_path)
            print(f"📄 Extracted {len(policy_text)} characters from PDF")
            
            if not policy_text or len(policy_text.strip()) < 50:
                print("⚠️ PDF appears to be empty or has very little text. Using default rules.")
                return self._get_default_rules()
            
            structured_rules = self._parse_policy_text(policy_text)
            
            print(f"✅ Successfully loaded policy rules from PDF")
            print(f"   - EL Rules: {len(structured_rules['EL'])} parameters")
            print(f"   - SL Rules: {len(structured_rules['SL'])} parameters") 
            print(f"   - CL Rules: {len(structured_rules['CL'])} parameters")
            
            return structured_rules
            
        except Exception as e:
            print(f"❌ Error loading PDF: {e}")
            import traceback
            traceback.print_exc()
            return self._get_default_rules()
    
    def _extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file with better error handling"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                print(f"📑 PDF has {len(pdf_reader.pages)} pages")
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"Page {page_num + 1}: {page_text}\n\n"
                    else:
                        print(f"⚠️ Page {page_num + 1} appears to be empty or unreadable")
                
            return text
        except Exception as e:
            print(f"❌ Error reading PDF file: {e}")
            return ""
    
    def _parse_policy_text(self, policy_text):
        """Parse PDF text into structured policy rules with improved parsing"""
        # Initialize with default structure
        rules = self._get_default_rules()
        
        if not policy_text:
            return rules
        
        print("🔍 Parsing PDF content for policy rules...")
        
        # Convert to lowercase for easier matching but keep original for display
        text_lower = policy_text.lower()
        
        # Enhanced pattern matching for leave rules
        leave_patterns = {
            'EL': {
                'keywords': ['earned leave', 'el', 'annual leave', 'vacation leave'],
                'max_days': [r'earned leave.*?(\d+).*?days', r'el.*?(\d+).*?days', r'annual leave.*?(\d+)'],
                'notice': [r'notice.*?(\d+).*?days', r'advance.*?(\d+).*?days'],
                'carry_over': [r'carry over.*?(yes|no|allowed|not allowed)'],
                'purpose': [r'earned leave.*?for.*?([^.]*?\.)'],
                'min_days': [r'minimum.*?(\d+).*?days', r'at least.*?(\d+).*?days']
            },
            'SL': {
                'keywords': ['sick leave', 'sl', 'medical leave'],
                'max_days': [r'sick leave.*?(\d+).*?days', r'sl.*?(\d+).*?days', r'medical leave.*?(\d+)'],
                'notice': [r'sick leave.*?notice.*?(\d+)', r'immediate.*?sick'],
                'medical_certificate': [r'medical certificate.*?(required|not required)'],
                'purpose': [r'sick leave.*?for.*?([^.]*?\.)']
            },
            'CL': {
                'keywords': ['casual leave', 'cl', 'emergency leave'],
                'max_days': [r'casual leave.*?(\d+).*?days', r'cl.*?(\d+).*?days'],
                'notice': [r'casual leave.*?notice.*?(\d+)'],
                'max_consecutive': [r'maximum.*?(\d+).*?consecutive', r'not more than.*?(\d+).*?days'],
                'purpose': [r'casual leave.*?for.*?([^.]*?\.)']
            }
        }
        
        # Parse each leave type
        for leave_type, patterns in leave_patterns.items():
            # Check if this leave type is mentioned in the document
            type_found = any(keyword in text_lower for keyword in patterns['keywords'])
            
            if type_found:
                print(f"  ✅ Found {leave_type} rules in PDF")
                
                # Extract maximum days
                for pattern in patterns['max_days']:
                    matches = re.findall(pattern, text_lower, re.IGNORECASE)
                    if matches:
                        try:
                            rules[leave_type]['max_per_year'] = int(matches[0])
                            print(f"    - Max days: {matches[0]}")
                            break
                        except ValueError:
                            continue
                
                # Extract advance notice
                for pattern in patterns.get('notice', []):
                    matches = re.findall(pattern, text_lower, re.IGNORECASE)
                    if matches:
                        try:
                            rules[leave_type]['advance_notice'] = int(matches[0])
                            print(f"    - Advance notice: {matches[0]} days")
                            break
                        except ValueError:
                            continue
                
                # Extract minimum days for EL
                if 'min_days' in patterns and leave_type == 'EL':
                    for pattern in patterns['min_days']:
                        matches = re.findall(pattern, text_lower, re.IGNORECASE)
                        if matches:
                            try:
                                rules[leave_type]['min_days'] = int(matches[0])
                                print(f"    - Minimum days: {matches[0]} days")
                                break
                            except ValueError:
                                continue
                
                # Extract other rules
                if 'medical_certificate' in patterns:
                    for pattern in patterns['medical_certificate']:
                        matches = re.findall(pattern, text_lower, re.IGNORECASE)
                        if matches:
                            rules[leave_type]['medical_certificate'] = matches[0]
                            print(f"    - Medical certificate: {matches[0]}")
                
                if 'max_consecutive' in patterns:
                    for pattern in patterns['max_consecutive']:
                        matches = re.findall(pattern, text_lower, re.IGNORECASE)
                        if matches:
                            try:
                                rules[leave_type]['max_consecutive'] = int(matches[0])
                                print(f"    - Max consecutive: {matches[0]} days")
                            except ValueError:
                                continue
            
            else:
                print(f"  ⚠️ {leave_type} not found in PDF, using defaults")
        
        # Extract contact information if present
        contact_patterns = {
            'hr_email': [r'hr.*?@.*?\.com', r'email.*?@.*?\.com', r'contact.*?@.*?\.com'],
            'hr_phone': [r'phone.*?(\d{10})', r'contact.*?(\d{10})', r'\b\d{10}\b'],
            'hr_name': [r'hr manager.*?([a-zA-Z ]+)', r'human resources.*?([a-zA-Z ]+)']
        }
        
        for contact_type, patterns in contact_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, policy_text, re.IGNORECASE)
                if matches:
                    self.contact_info[contact_type] = matches[0]
                    print(f"  📞 Found {contact_type}: {matches[0]}")
        
        return rules
    
    def _load_contact_info(self):
        """Load default contact information"""
        return {
            'hr_email': 'hr@company.com',
            'hr_phone': '+1-555-0123',
            'hr_name': 'HR Department',
            'hr_hours': 'Monday-Friday, 9 AM - 6 PM',
            'emergency_contact': 'For urgent issues, call +1-555-EMERGENCY'
        }
    
    def _get_default_rules(self):
        """Provide default rules if PDF parsing fails"""
        return {
            "EL": {
                "max_per_year": 12,
                "advance_notice": 2,
                "min_days": 3,
                "purpose": "Vacations, personal work, planned time off",
                "carry_over": "Yes, maximum 30 days",
                "description": "Earned Leave for planned absences - Minimum 3 days at a time",
                "date_range": "±30 days from current date"
            },
            "SL": {
                "max_per_year": 7,
                "advance_notice": 0,
                "purpose": "Medical reasons, health issues, sickness",
                "carry_over": "No",
                "medical_certificate": "Required for more than 3 consecutive days",
                "description": "Sick Leave for health-related absences",
                "date_range": "Past dates only (up to 15 days before)"
            },
            "CL": {
                "max_per_year": 5,
                "advance_notice": 1,
                "purpose": "Personal emergencies, urgent work",
                "carry_over": "No",
                "max_consecutive": 2,
                "description": "Casual Leave for urgent personal matters",
                "date_range": "±30 days from current date"
            },
            "general": {
                "application_procedure": "Apply through system with manager approval",
                "approval_process": "Immediate supervisor approval required",
                "emergency_leave": "Can be applied same day for genuine emergencies"
            }
        }
    
    def _validate_leave_dates(self, leave_type, leave_dates):
        """Validate dates based on leave type rules with better flexibility"""
        today = datetime.now().date()
        validation_errors = []
        
        if not leave_dates:
            validation_errors.append("❌ **No valid dates found in your request.**")
            validation_errors.append("💡 Please specify dates like: 'yesterday', 'last Monday', '7-10-2025', or 'next week'")
            return validation_errors
        
        for leave_date in leave_dates:
            if leave_type == 'SL':
                # SL: Only past dates (up to 15 days before) - but allow same day
                if leave_date > today:
                    validation_errors.append(f"❌ **SL Date Restriction:** Sick Leave cannot be applied for future dates.")
                    validation_errors.append(f"   Requested: {leave_date.strftime('%Y-%m-%d')} (Future)")
                    validation_errors.append(f"   Allowed: Only past dates and today (up to 15 days before)")
                    break
                elif (today - leave_date).days > 15:
                    validation_errors.append(f"❌ **SL Date Restriction:** Sick Leave cannot be applied for dates more than 15 days in the past.")
                    validation_errors.append(f"   Requested: {leave_date.strftime('%Y-%m-%d')} ({(today - leave_date).days} days ago)")
                    validation_errors.append(f"   Allowed: Maximum 15 days before today")
                    break
            
            elif leave_type == 'EL':
                # EL: ±30 days from current date
                days_diff = (leave_date - today).days
                if abs(days_diff) > 30:
                    if days_diff > 0:
                        validation_errors.append(f"❌ **EL Date Restriction:** Earned Leave cannot be applied more than 30 days in advance.")
                    else:
                        validation_errors.append(f"❌ **EL Date Restriction:** Earned Leave cannot be applied for dates more than 30 days in the past.")
                    validation_errors.append(f"   Requested: {leave_date.strftime('%Y-%m-%d')} ({abs(days_diff)} days {'ahead' if days_diff > 0 else 'ago'})")
                    validation_errors.append(f"   Allowed: Within 30 days from today ({today.strftime('%Y-%m-%d')})")
                    break
            
            elif leave_type == 'CL':
                # CL: ±30 days from current date
                days_diff = (leave_date - today).days
                if abs(days_diff) > 30:
                    if days_diff > 0:
                        validation_errors.append(f"❌ **CL Date Restriction:** Casual Leave cannot be applied more than 30 days in advance.")
                    else:
                        validation_errors.append(f"❌ **CL Date Restriction:** Casual Leave cannot be applied for dates more than 30 days in the past.")
                    validation_errors.append(f"   Requested: {leave_date.strftime('%Y-%m-%d')} ({abs(days_diff)} days {'ahead' if days_diff > 0 else 'ago'})")
                    validation_errors.append(f"   Allowed: Within 30 days from today ({today.strftime('%Y-%m-%d')})")
                    break
        
        return validation_errors
    
    def query_policy(self, question):
        """Answer policy questions using PDF-based knowledge"""
        question_lower = question.lower()
        
        # Contact information queries
        if any(word in question_lower for word in ['contact', 'hr', 'human resources', 'email', 'phone', 'call', 'reach']):
            return self._format_contact_response(), ["rules.pdf"]
        
        # Date restriction queries
        if any(word in question_lower for word in ['when can i apply', 'date restriction', 'time limit', 'advance notice']):
            return self._format_date_restrictions_response(), ["rules.pdf"]
        
        # EL (Earned Leave) queries
        if any(word in question_lower for word in ['el', 'earned leave', 'earned', 'vacation']):
            rules = self.policy_knowledge["EL"]
            answer = self._format_el_response(rules)
        
        # SL (Sick Leave) queries
        elif any(word in question_lower for word in ['sl', 'sick leave', 'sick', 'medical', 'illness']):
            rules = self.policy_knowledge["SL"]
            answer = self._format_sl_response(rules)
        
        # CL (Casual Leave) queries
        elif any(word in question_lower for word in ['cl', 'casual leave', 'casual', 'emergency', 'personal leave']):
            rules = self.policy_knowledge["CL"]
            answer = self._format_cl_response(rules)
        
        # General policy queries
        elif any(word in question_lower for word in ['policy', 'rule', 'how to apply', 'procedure']):
            answer = self._format_general_response()
        
        # Specific number queries
        elif any(word in question_lower for word in ['how many', 'entitlement', 'days']):
            answer = self._handle_entitlement_query(question_lower)
        
        # Minimum days queries
        elif any(word in question_lower for word in ['minimum', 'min days', 'at least']):
            answer = self._handle_minimum_days_query(question_lower)
        
        else:
            answer = self._handle_general_query(question)
        
        return answer, ["rules.pdf"]
    
    def _format_date_restrictions_response(self):
        """Format date restrictions response"""
        return f"""📅 **Leave Application Date Restrictions**

**Earned Leave (EL):**
• 🗓️ Date Range: Within 30 days before/after current date
• ⏰ Advance Notice: {self.policy_knowledge['EL'].get('advance_notice', 2)} days
• 📏 Minimum Duration: {self.policy_knowledge['EL'].get('min_days', 3)} consecutive days
• ❌ Not Allowed: Single day or 2-day applications

**Sick Leave (SL):**
• 🗓️ Date Range: Past dates only (up to 15 days before)
• ⏰ Advance Notice: Same day application allowed
• ❌ Not Allowed: Future dates

**Casual Leave (CL):**
• 🗓️ Date Range: Within 30 days before/after current date
• ⏰ Advance Notice: {self.policy_knowledge['CL'].get('advance_notice', 1)} day
• 📏 Maximum Consecutive: {self.policy_knowledge['CL'].get('max_consecutive', 2)} days

**Today's Date:** {datetime.now().strftime('%Y-%m-%d')}

💡 *All date restrictions are calculated from today's date*"""
    
    def _format_contact_response(self):
        """Format HR contact information response"""
        return f"""📞 **HR Contact Information**

**Human Resources Department:**
• 📧 Email: {self.contact_info['hr_email']}
• 📞 Phone: {self.contact_info['hr_phone']}
• 👤 Contact: {self.contact_info['hr_name']}
• 🕒 Hours: {self.contact_info['hr_hours']}

**For Leave-Related Queries:**
• Leave policy clarifications
• Special leave requests
• Emergency situations
• Policy exceptions

**Emergency Contact:**
{self.contact_info['emergency_contact']}

💡 *Please contact HR for any policy-related questions or special circumstances not covered in the standard policy.*"""
    
    def _format_el_response(self, rules):
        """Format EL policy response with minimum days requirement"""
        min_days = rules.get('min_days', 3)
        return f"""🏖️ **Earned Leave (EL) Policy - From Company Rules**

• **Maximum per year:** {rules.get('max_per_year', 12)} days
• **Date Range:** Within 30 days before/after current date
• **Minimum duration:** {min_days} days at a time
• **Advance notice:** {rules.get('advance_notice', 2)} days
• **Purpose:** {rules.get('purpose', 'Vacations, personal work')}
• **Carry over:** {rules.get('carry_over', 'Yes, max 30 days')}

🚫 **Important Restrictions:**
- Single day or 2-day EL applications are **NOT allowed**
- Minimum {min_days} consecutive days required
- Cannot apply more than 30 days in advance
- Cannot apply for dates more than 30 days in past

💡 *EL is for extended planned vacations within 30-day window*

📞 *For specific EL queries, contact {self.contact_info['hr_email']}*"""
    
    def _format_sl_response(self, rules):
        """Format SL policy response"""
        return f"""🤒 **Sick Leave (SL) Policy - From Company Rules**

• **Maximum per year:** {rules.get('max_per_year', 7)} days
• **Date Range:** Past dates only (up to 15 days before)
• **Advance notice:** {rules.get('advance_notice', 0)} days (can apply same day)
• **Purpose:** {rules.get('purpose', 'Medical reasons, health issues')}
• **Carry over:** {rules.get('carry_over', 'No')}
• **Medical certificate:** {rules.get('medical_certificate', 'Required for >3 consecutive days')}

🚫 **Important Restrictions:**
- Future dates are **NOT allowed**
- Maximum 15 days in the past
- Same day application only for current illness

💡 *SL is for health-related absences that already occurred*

📞 *For medical emergencies, contact {self.contact_info['hr_phone']}*"""
    
    def _format_cl_response(self, rules):
        """Format CL policy response"""
        return f"""🎯 **Casual Leave (CL) Policy - From Company Rules**

• **Maximum per year:** {rules.get('max_per_year', 5)} days
• **Date Range:** Within 30 days before/after current date
• **Advance notice:** {rules.get('advance_notice', 1)} days
• **Purpose:** {rules.get('purpose', 'Personal emergencies only')}
• **Carry over:** {rules.get('carry_over', 'No')}
• **Max consecutive days:** {rules.get('max_consecutive', 2)}

🚫 **Important Restrictions:**
- Cannot apply more than 30 days in advance
- Cannot apply for dates more than 30 days in past
- Maximum 2 consecutive days

💡 *CL is for urgent personal emergencies within 30-day window*

📞 *For urgent leave requests, call {self.contact_info['hr_phone']}*"""
    
    def _format_general_response(self):
        """Format general policy response"""
        general = self.policy_knowledge["general"]
        min_el_days = self.policy_knowledge['EL'].get('min_days', 3)
        return f"""📚 **Company Leave Policy Summary - From Official Rules**

**Available Leave Types:**

🏖️ **EL (Earned Leave)**
• {self.policy_knowledge['EL'].get('max_per_year', 12)} days/year • ±30 days window • Min {min_el_days} days • {self.policy_knowledge['EL'].get('advance_notice', 2)} days notice

🤒 **SL (Sick Leave)**  
• {self.policy_knowledge['SL'].get('max_per_year', 7)} days/year • Past dates only (15 days max) • Same day application

🎯 **CL (Casual Leave)**
• {self.policy_knowledge['CL'].get('max_per_year', 5)} days/year • ±30 days window • Max 2 consecutive • {self.policy_knowledge['CL'].get('advance_notice', 1)} day notice

**Important Restrictions:**
🚫 Single day or 2-day EL applications NOT permitted
🚫 SL future dates NOT allowed
🚫 Applications outside date windows NOT permitted

**General Rules:**
• {general.get('application_procedure', 'Apply through system only')}
• {general.get('approval_process', 'Manager approval required')}
• No overlapping leaves
• Balance must be available

**Need Help?**
📞 Contact HR: {self.contact_info['hr_email']} | {self.contact_info['hr_phone']}"""
    
    def _handle_entitlement_query(self, question):
        """Handle specific entitlement questions"""
        if 'el' in question:
            days = self.policy_knowledge['EL'].get('max_per_year', 12)
            min_days = self.policy_knowledge['EL'].get('min_days', 3)
            return f"📊 According to company policy, you're entitled to **{days} EL (Earned Leave) days** per year.\n\n🚫 **Restrictions:** Min {min_days} days at a time • ±30 days window\n\n📞 For entitlement verification, contact {self.contact_info['hr_email']}"
        
        elif 'sl' in question:
            days = self.policy_knowledge['SL'].get('max_per_year', 7)
            return f"📊 According to company policy, you're entitled to **{days} SL (Sick Leave) days** per year.\n\n🚫 **Restrictions:** Past dates only • Max 15 days before\n\n📞 For medical leave queries, contact {self.contact_info['hr_phone']}"
        
        elif 'cl' in question:
            days = self.policy_knowledge['CL'].get('max_per_year', 5)
            return f"📊 According to company policy, you're entitled to **{days} CL (Casual Leave) days** per year.\n\n🚫 **Restrictions:** ±30 days window • Max 2 consecutive days\n\n📞 For emergency leave, call {self.contact_info['hr_phone']}"
        
        else:
            el_days = self.policy_knowledge['EL'].get('max_per_year', 12)
            sl_days = self.policy_knowledge['SL'].get('max_per_year', 7)
            cl_days = self.policy_knowledge['CL'].get('max_per_year', 5)
            min_el_days = self.policy_knowledge['EL'].get('min_days', 3)
            return f"""📊 **Leave Entitlement (From Company Policy):**

• 🏖️ EL (Earned Leave): {el_days} days/year (min {min_el_days} days, ±30 days)
• 🤒 SL (Sick Leave): {sl_days} days/year (past dates only, 15 days max)  
• 🎯 CL (Casual Leave): {cl_days} days/year (±30 days, max 2 consecutive)
• 📈 Total: {el_days + sl_days + cl_days} days annually

**HR Contact:**
📧 {self.contact_info['hr_email']} | 📞 {self.contact_info['hr_phone']}"""
    
    def _handle_minimum_days_query(self, question):
        """Handle minimum days queries"""
        if 'el' in question or 'earned' in question:
            min_days = self.policy_knowledge['EL'].get('min_days', 3)
            return f"""📋 **EL Minimum Duration Rule**

According to company policy:

🚫 **Earned Leave (EL) Restrictions:**
- Single day EL applications: **NOT ALLOWED**
- 2-day EL applications: **NOT ALLOWED**
- Minimum requirement: **{min_days} consecutive days**
- Date window: **±30 days from today**

💡 **Alternative Options:**
- For 1-2 day planned leaves: Use **CL (Casual Leave)**
- For medical/sick leaves: Use **SL (Sick Leave)**
- For emergencies: Use **CL (Casual Leave)**

📞 *For exceptions, contact HR: {self.contact_info['hr_email']}*"""
        
        else:
            min_el_days = self.policy_knowledge['EL'].get('min_days', 3)
            return f"""📋 **Minimum Leave Duration Rules**

**Earned Leave (EL):**
• Minimum {min_el_days} consecutive days required
• Single day or 2-day EL: **NOT PERMITTED**
• Date window: ±30 days from today

**Sick Leave (SL):**
• No minimum duration
• Can be applied for single days
• Past dates only (max 15 days before)

**Casual Leave (CL):**
• Maximum 2 consecutive days
• Can be applied for single days
• Date window: ±30 days from today

💡 *Use CL or SL for shorter duration leaves*"""
    
    def _handle_general_query(self, question):
        """Handle general queries"""
        min_el_days = self.policy_knowledge['EL'].get('min_days', 3)
        return f"""🤔 I understand you're asking about: "{question}"

I can help you with information from the company leave policy document about:

• 🏖️ Earned Leave (EL) policies - Minimum {min_el_days} days, ±30 days window
• 🤒 Sick Leave (SL) rules - Past dates only, 15 days max  
• 🎯 Casual Leave (CL) guidelines - ±30 days window, max 2 days
• 📊 Your personal leave balance and entitlements
• 📝 Leave application procedures and approval process
• 📞 HR contact information and support

**Important Restrictions:**
🚫 Single day or 2-day EL applications are NOT allowed
🚫 SL future dates are NOT allowed
🚫 Applications outside date windows are NOT permitted

**Need Human Assistance?**
📧 Email: {self.contact_info['hr_email']}
📞 Phone: {self.contact_info['hr_phone']}

All responses are based on the official company policy PDF document.

Try asking specifically about leave types or policy details!"""


class LeaveAgent:
    def __init__(self, database, rag_system):
        self.db = database
        self.rag = rag_system
    
    def process_message(self, user_id, message):
        """Process user message with PDF-based policy responses"""
        # Save user message to database
        self.db.save_chat_message(user_id, 'user', message)
        
        message_lower = message.lower()
        
        # Handle policy queries (including contact info)
        if any(word in message_lower for word in ['policy', 'rule', 'how many', 'entitlement', 'can i', 'what is', 'how to', 'contact', 'hr', 'email', 'phone', 'minimum', 'when can i apply', 'date restriction']):
            answer, sources = self.rag.query_policy(message)
        
        # Handle balance inquiries
        elif any(word in message_lower for word in ['balance', 'remaining', 'left', 'available']):
            answer = self._get_balance_response(user_id)
        
        # Handle leave applications
        elif any(word in message_lower for word in ['apply', 'leave', 'vacation', 'off', 'holiday']):
            answer = self._handle_leave_application(user_id, message)
        
        # Handle status inquiries
        elif any(word in message_lower for word in ['status', 'pending', 'approved', 'my leaves']):
            answer = self._get_status_response(user_id)
        
        # Greeting
        elif any(word in message_lower for word in ['hi', 'hello', 'hey']):
            answer = self._get_greeting_response(user_id)
        
        # Help
        elif any(word in message_lower for word in ['help', 'what can you do']):
            answer = self._get_help_response()
        
        # Clear chat history
        elif any(word in message_lower for word in ['clear chat', 'clear history', 'reset chat']):
            answer = self._clear_chat_history(user_id)
        
        else:
            # Use policy system for general queries
            answer, sources = self.rag.query_policy(message)
        
        # Save assistant response to database
        self.db.save_chat_message(user_id, 'assistant', answer)
        
        return answer
    
    def get_chat_history(self, user_id):
        """Get formatted chat history for display"""
        chat_records = self.db.get_chat_history(user_id)
        
        if not chat_records:
            return []
        
        # Convert to Gradio chat format
        gradio_history = []
        current_user_msg = None
        
        for record in chat_records:
            if record['Role'] == 'user':
                current_user_msg = record['Message']
            elif record['Role'] == 'assistant' and current_user_msg is not None:
                gradio_history.append([current_user_msg, record['Message']])
                current_user_msg = None
        
        return gradio_history
    
    def _clear_chat_history(self, user_id):
        """Clear chat history for user"""
        success = self.db.clear_chat_history(user_id)
        if success:
            return "🗑️ **Chat history cleared!**\n\nYour conversation history has been reset. Start a new conversation!"
        else:
            return "❌ **Failed to clear chat history**\n\nThere was an error clearing your chat history. Please try again."
    
    # ... keep all the other existing methods unchanged (_parse_leave_request, _handle_leave_application, etc.) ...
    
    def _parse_leave_request(self, message, user_id):
        """Parse leave application from natural language with improved date detection"""
        message_lower = message.lower().strip()
        
        print(f"🔍 Processing leave request: '{message_lower}'")
        
        # Determine leave type
        leave_type = None
        if any(word in message_lower for word in ['el', 'earned leave', 'earned', 'vacation']):
            leave_type = 'EL'
        elif any(word in message_lower for word in ['sl', 'sick leave', 'sick', 'medical', 'fever', 'illness']):
            leave_type = 'SL'
        elif any(word in message_lower for word in ['cl', 'casual leave', 'casual', 'emergency', 'personal leave']):
            leave_type = 'CL'
        
        print(f"📋 Detected leave type: {leave_type}")
        
        # Parse dates using multiple strategies
        leave_dates = self._extract_dates_from_message(message_lower)
        duration_days = len(leave_dates) if leave_dates else 1
        
        # Parse reason
        reason = self._extract_reason_from_message(message_lower)
        
        print(f"✅ Final parsing result: Type={leave_type}, Dates={leave_dates}, Duration={duration_days}, Reason={reason}")
        
        return leave_type, leave_dates, duration_days, reason

    def _extract_dates_from_message(self, message):
        """Extract dates from natural language message"""
        today = datetime.now().date()
        leave_dates = []
        
        # Clean the message for date parsing - be more aggressive
        clean_message = message
        
        # Remove common application phrases
        remove_phrases = [
            'i want to apply', 'apply for', 'i need', 'want to take', 'take', 
            'leave', 'sl', 'el', 'cl', 'sick', 'earned', 'casual', 'medical',
            'apply', 'for'
        ]
        
        for phrase in remove_phrases:
            # Replace with space to avoid joining words
            clean_message = clean_message.replace(phrase, ' ')
        
        # Clean up multiple spaces
        clean_message = ' '.join(clean_message.split())
        clean_message = clean_message.strip()
        
        print(f"🔍 Cleaned message for date parsing: '{clean_message}'")
        
        # Check for date range first (most specific pattern)
        date_range = self._parse_date_range(clean_message)
        if date_range:
            leave_dates = date_range
            print(f"✅ Date range pattern → {len(leave_dates)} days: {leave_dates[0]} to {leave_dates[-1]}")
            return leave_dates
        
        # Strategy 1: Handle specific patterns
        
        # "before monday" pattern
        if 'before' in clean_message:
            parts = clean_message.split('before')
            if len(parts) > 1:
                day_str = parts[1].strip()
                target_date = self._parse_relative_day(day_str)
                if target_date:
                    leave_date = target_date - timedelta(days=1)
                    leave_dates = [leave_date]
                    print(f"✅ 'Before' pattern: {day_str} → {leave_date}")
                    return leave_dates
        
        # "last monday" pattern
        if 'last' in clean_message:
            day_str = clean_message.replace('last', '').strip()
            leave_date = self._parse_relative_day(day_str, past=True)
            if leave_date:
                leave_dates = [leave_date]
                print(f"✅ 'Last' pattern: {day_str} → {leave_date}")
                return leave_dates
        
        # "yesterday" pattern
        if 'yesterday' in clean_message:
            leave_dates = [today - timedelta(days=1)]
            print(f"✅ 'Yesterday' pattern → {leave_dates[0]}")
            return leave_dates
        
        # "today" pattern
        if 'today' in clean_message:
            leave_dates = [today]
            print(f"✅ 'Today' pattern → {leave_dates[0]}")
            return leave_dates
        
        # "tomorrow" pattern
        if 'tomorrow' in clean_message:
            leave_dates = [today + timedelta(days=1)]
            print(f"✅ 'Tomorrow' pattern → {leave_dates[0]}")
            return leave_dates
        
        # Single date pattern
        single_date = self._parse_single_date(clean_message)
        if single_date:
            leave_dates = [single_date]
            print(f"✅ Single date pattern → {leave_dates[0]}")
            return leave_dates
        
        # Day of week pattern
        day_date = self._parse_day_of_week(clean_message)
        if day_date:
            leave_dates = [day_date]
            print(f"✅ Day of week pattern → {leave_dates[0]}")
            return leave_dates
        
        # Final attempt: Try parsing the original message directly
        print("🔍 Final attempt: parsing original message directly")
        single_date_final = self._parse_single_date(message)
        if single_date_final:
            leave_dates = [single_date_final]
            print(f"✅ Final single date attempt → {leave_dates[0]}")
            return leave_dates
        
        print("❌ No dates could be parsed from the message")
        return []

    def _parse_relative_day(self, day_str, past=False):
        """Parse relative day patterns like 'monday', 'tuesday' etc."""
        today = datetime.now().date()
        
        days_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6,
            'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
        }
        
        for day_name, day_num in days_map.items():
            if day_name in day_str.lower():
                # Calculate days to target day
                days_ahead = (day_num - today.weekday()) % 7
                
                if past:
                    # For "last monday", find the most recent past occurrence
                    if days_ahead == 0:
                        days_ahead = 7  # Go back one week
                    target_date = today - timedelta(days=days_ahead)
                else:
                    # For "before monday", find the next occurrence
                    if days_ahead == 0:
                        days_ahead = 7  # Go to next week
                    target_date = today + timedelta(days=days_ahead)
                
                return target_date
        
        return None

    def _parse_date_range(self, message):
        """Parse date ranges like '7-10-2025 to 10-10-2025'"""
        today = datetime.now().date()
        
        # Try different separators
        separators = [' to ', ' till ', ' until ', ' - ', ' through ']
        for separator in separators:
            if separator in message:
                parts = message.split(separator)
                if len(parts) >= 2:
                    start_str = parts[0].strip()
                    end_str = parts[1].strip()
                    
                    print(f"🔍 Parsing date range: '{start_str}' {separator} '{end_str}'")
                    
                    # Try different date formats - prioritize DD-MM-YYYY format
                    date_formats = [
                        '%d-%m-%Y', '%d/%m/%Y', '%d-%m', '%d/%m',  # DD-MM formats first
                        '%m-%d-%Y', '%m/%d/%Y', '%m-%d', '%m/%d',  # MM-DD formats
                        '%Y-%m-%d'
                    ]
                    
                    start_date = None
                    end_date = None
                    
                    # First try with explicit formats
                    for fmt in date_formats:
                        try:
                            if not start_date:
                                start_date = datetime.strptime(start_str, fmt).date()
                                # If year not specified, use current year
                                if start_date.year == 1900:
                                    start_date = start_date.replace(year=today.year)
                            if not end_date:
                                end_date = datetime.strptime(end_str, fmt).date()
                                if end_date.year == 1900:
                                    end_date = end_date.replace(year=today.year)
                        except ValueError:
                            continue
                    
                    # If that fails, try dateparser as fallback
                    if not start_date:
                        start_date_parsed = dateparser.parse(start_str)
                        if start_date_parsed:
                            start_date = start_date_parsed.date()
                    
                    if not end_date:
                        end_date_parsed = dateparser.parse(end_str)
                        if end_date_parsed:
                            end_date = end_date_parsed.date()
                    
                    print(f"🔍 Parsed dates - Start: {start_date}, End: {end_date}")
                    
                    if start_date and end_date and start_date <= end_date:
                        # Generate all dates in range
                        dates = []
                        current = start_date
                        while current <= end_date:
                            dates.append(current)
                            current += timedelta(days=1)
                        print(f"✅ Date range successfully parsed: {len(dates)} days")
                        return dates
                    else:
                        print(f"❌ Date range parsing failed - Start: {start_date}, End: {end_date}")
        
        return None
    def _parse_single_date(self, message):
        """Parse single date patterns"""
        today = datetime.now().date()
        
        # Try specific formats first - prioritize DD-MM-YYYY
        date_formats = [
            '%d-%m-%Y', '%d/%m/%Y',  # DD-MM-YYYY formats first
            '%d-%m', '%d/%m',        # DD-MM formats (current year)
            '%m-%d-%Y', '%m/%d/%Y',  # MM-DD-YYYY formats
            '%m-%d', '%m/%d',        # MM-DD formats (current year)
            '%Y-%m-%d'               # YYYY-MM-DD format
        ]
        
        for fmt in date_formats:
            try:
                # Try to find date pattern in the message
                date_pattern = r'\b\d{1,2}[-/]\d{1,2}[-/]?\d{0,4}\b'
                matches = re.findall(date_pattern, message)
                if matches:
                    date_str = matches[0]
                    date_obj = datetime.strptime(date_str, fmt).date()
                    # If year not specified, use current year
                    if date_obj.year == 1900:
                        date_obj = date_obj.replace(year=today.year)
                    print(f"✅ Single date parsed with format {fmt}: {date_str} → {date_obj}")
                    return date_obj
            except ValueError:
                continue
        
        # Try dateparser as fallback
        parsed = dateparser.parse(message)
        if parsed:
            print(f"✅ Single date parsed with dateparser: {parsed.date()}")
            return parsed.date()
        
        return None

    def _parse_day_of_week(self, message):
        """Parse simple day of week"""
        today = datetime.now().date()
        
        days_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6,
            'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
        }
        
        for day_name, day_num in days_map.items():
            if day_name in message.lower():
                days_ahead = (day_num - today.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Next week
                return today + timedelta(days=days_ahead)
        
        return None

    def _extract_reason_from_message(self, message):
        """Extract reason from the message"""
        message_lower = message.lower()
        
        if 'vacation' in message_lower:
            return "Vacation"
        elif any(word in message_lower for word in ['sick', 'medical', 'ill', 'hospital', 'doctor', 'fever', 'health', 'not well']):
            return "Medical"
        elif any(word in message_lower for word in ['emergency', 'urgent', 'personal']):
            return "Personal Emergency"
        elif any(word in message_lower for word in ['family', 'relative', 'parent']):
            return "Family Matter"
        elif any(word in message_lower for word in ['wedding', 'marriage']):
            return "Wedding"
        elif any(word in message_lower for word in ['festival', 'celebration', 'holiday', 'diwali', 'christmas']):
            return "Festival/Celebration"
        else:
            return "Personal"

    def _handle_leave_application(self, user_id, message):
        """Handle leave application process with all validations"""
        # Parse the leave request
        leave_type, leave_dates, duration_days, reason = self._parse_leave_request(message, user_id)
        
        # Check if we have enough information
        if not leave_type:
            return """❌ **Missing Leave Type**

I need to know what type of leave you're applying for:
- 🏖️ **EL** (Earned Leave) - for vacations (min 3 days, ±30 days)
- 🤒 **SL** (Sick Leave) - for medical reasons (past dates only)  
- 🎯 **CL** (Casual Leave) - for emergencies (±30 days, max 2 days)

**Try these formats:**
"Apply SL for yesterday"
"Apply EL for 3 days from 25-12-2024 to 27-12-2024"
"Apply CL for tomorrow"

📞 *Need help? Contact HR at hr@company.com*"""
        
        if not leave_dates:
            return f"""❌ **Could not understand the dates in your request**

I couldn't figure out which date(s) you want to apply leave for.

**Please try these formats:**
• "Apply {leave_type} for yesterday"
• "Apply {leave_type} for last Monday" 
• "Apply {leave_type} for 25-12-2024"
• "Apply {leave_type} for 25-12-2024 to 27-12-2024"

**Examples that work:**
• "Apply SL for yesterday" → Sick leave for yesterday
• "Apply EL for 25-12-2024 to 27-12-2024" → 3-day earned leave
• "Apply CL for tomorrow" → Casual leave for tomorrow

📞 *Need help? Contact HR at hr@company.com*"""
        
        # Validate dates based on leave type
        date_validation_errors = self.rag._validate_leave_dates(leave_type, leave_dates)
        if date_validation_errors:
            return "\n".join(date_validation_errors) + f"\n\n📞 *For date-related exceptions, contact HR: {self.rag.contact_info['hr_email']}*"
        
        # Check EL minimum days restriction
        if leave_type == 'EL' and duration_days < 3:
            return f"""❌ **EL Minimum Duration Violation**

🚫 **Earned Leave Policy Restriction:**
- Single day EL: NOT ALLOWED
- 2-day EL: NOT ALLOWED  
- Minimum requirement: 3 consecutive days

📋 **Your Request:** {duration_days} day{'s' if duration_days > 1 else ''} EL

💡 **Suggested Alternatives:**
- For {duration_days} day{'s' if duration_days > 1 else ''}: Use **CL (Casual Leave)** instead
- For medical reasons: Use **SL (Sick Leave)**
- Need 3+ days vacation: Apply for proper EL duration

**Try:**
"Apply for CL {message.split('for')[-1] if 'for' in message else 'tomorrow'}"

📞 *For EL policy exceptions, contact HR: hr@company.com*"""
        
        # Check balance
        balance = self.db.get_user_balance(user_id)
        if not balance or balance[leave_type] < duration_days:
            return f"""❌ **Insufficient {leave_type} Balance**

You don't have enough {leave_type} days available.
Your request: {duration_days} day{'s' if duration_days > 1 else ''}
Your current balance: {balance[leave_type] if balance else 0} {leave_type} days

📊 **Your Current Balance:**
• EL: {balance['EL'] if balance else 0} days
• SL: {balance['SL'] if balance else 0} days  
• CL: {balance['CL'] if balance else 0} days

📞 *Contact HR for balance-related queries: hr@company.com*"""
        
        # Check date overlap for all dates
        for leave_date in leave_dates:
            if self.db.check_date_overlap(user_id, leave_date.strftime('%Y-%m-%d 00:00:00')):
                return f"""❌ **Date Conflict**

You already have a leave application or approved leave for {leave_date.strftime('%Y-%m-%d')}.

Please choose different dates or check your existing applications.

📞 *For date conflict resolution, contact HR*"""
        
        # Apply for leave - process all dates
        successful_applications = 0
        application_details = []
        
        for leave_date in leave_dates:
            success = self.db.add_leave_request(
                user_id=user_id,
                leave_date=leave_date.strftime('%Y-%m-%d 00:00:00'),
                leave_type=leave_type,
                reason=reason,
                duration="Full Day"
            )
            
            if success:
                successful_applications += 1
                application_details.append(leave_date.strftime('%Y-%m-%d'))
            else:
                return f"""❌ **Application Partially Failed**

Successfully applied for {successful_applications} days, but failed for {leave_date.strftime('%Y-%m-%d')}.

Please try again or contact support.

📞 **HR Support:** hr@company.com | +1-555-0123"""
        
        if successful_applications > 0:
            date_range = application_details[0]
            if len(application_details) > 1:
                date_range = f"{application_details[0]} to {application_details[-1]}"
            
            return f"""✅ **Leave Application Submitted Successfully!**

📋 **Application Details:**
• **Type:** {leave_type}
• **Date:** {date_range} ({successful_applications} day{'s' if successful_applications > 1 else ''})
• **Reason:** {reason}
• **Status:** ⏳ Pending Approval
• **Balance After Approval:** {balance[leave_type] - successful_applications} {leave_type} days

📊 **Your Current Balance (Before Approval):**
• EL: {balance['EL']} days
• SL: {balance['SL']} days  
• CL: {balance['CL']} days

⏳ **Next Steps:**
- Your manager will review and approve your request
- Balance will be deducted only after approval
- You can check status anytime by asking "my leave status"

📞 *For application issues, contact HR at hr@company.com*"""
        else:
            return """❌ **Application Failed**

There was an error submitting your leave application. Please try again or contact support.

📞 **HR Support:** hr@company.com | +1-555-0123"""
    
    def _get_balance_response(self, user_id):
        """Get balance response"""
        balance = self.db.get_user_balance(user_id)
        if balance:
            return f"""📊 **Your Leave Balance:**

• 🏖️ EL (Earned Leave): {balance['EL']} days (min 3 days, ±30 days)
• 🤒 SL (Sick Leave): {balance['SL']} days (past dates only)  
• 🎯 CL (Casual Leave): {balance['CL']} days (±30 days, max 2 days)
• 📈 Total Leaves: {balance['TL']} days

💡 *Date restrictions apply to all leave types*

📞 *For balance disputes, contact HR at hr@company.com*"""
        return "❌ Unable to fetch your leave balance. Please make sure you're logged in correctly.\n\n📞 Contact HR for assistance: hr@company.com"
    
    def _get_status_response(self, user_id):
        """Get leave status response"""
        requests = self.db.get_user_leave_requests(user_id)
        if requests:
            response = "📋 **Your Leave Applications:**\n\n"
            for req in reversed(requests[-5:]):
                status_icon = "✅" if req['Status'] == 'Approved' else "❌" if req['Status'] == 'Rejected' else "⏳"
                date_str = req['Leave_Date'].split()[0] if ' ' in str(req['Leave_Date']) else str(req['Leave_Date'])
                response += f"{status_icon} **{date_str}** - {req['LeaveType']} - **{req['Status']}**\n"
                if req['Status'] == 'Pending':
                    response += f"   📝 Reason: {req['Reason']}\n"
                response += "\n"
            
            response += "📞 *For status inquiries, contact your manager or HR at hr@company.com*"
            return response
        else:
            return "📋 **No leave applications found.**\n\nYou haven't applied for any leaves yet.\n\n📞 *Contact HR for leave policy information: hr@company.com*"
    
    def _get_greeting_response(self, user_id):
        """Get greeting response"""
        balance = self.db.get_user_balance(user_id)
        if balance:
            return f"""👋 **Hello! I'm your AI Leave Management Assistant**

📊 **Your Current Balance:**
• EL: {balance['EL']} days (min 3 days) • SL: {balance['SL']} days • CL: {balance['CL']} days

I can help you with information from the company leave policy about:
• 🤔 Leave policy questions (from official PDF)
• 📝 Leave applications with date restrictions  
• 📊 Balance inquiries
• 📋 Application status
• 📚 Policy explanations
• 📞 HR contact information

**Important Date Restrictions:**
• EL: ±30 days window, min 3 days
• SL: Past dates only (15 days max)
• CL: ±30 days window, max 2 days

**Quick Examples:**
- "What are the EL policy rules?"
- "Apply for SL yesterday for medical appointment"
- "Apply EL for 3 days vacation next week"
- "When can I apply for CL?"

**HR Support:** 📧 hr@company.com | 📞 +1-555-0123

What would you like assistance with today?"""
        else:
            return """👋 **Hello! I'm your AI Leave Management Assistant**

I'm here to help you with all leave-related matters using information from the company policy document including:
• Leave policy information from official rules
• Balance inquiries with date restrictions
• Application assistance
• Status checks
• HR contact information

**Important Date Restrictions:**
• EL: ±30 days, min 3 days
• SL: Past dates only
• CL: ±30 days, max 2 days

**HR Department:** 📧 hr@company.com | 📞 +1-555-0123

Please log in to access personalized features!"""
    
    def _get_help_response(self):
        """Get help response"""
        return """🤖 **AI Leave Assistant - Comprehensive Help**

**I can help you with information from the company policy document:**

📚 **Policy Information (From Official Rules):**
• Leave entitlements and rules from PDF
• EL minimum 3 days requirement
• Date restrictions for all leave types
• Eligibility criteria from company policy

📊 **Personal Management:**
• Check your leave balance
• Apply for new leaves with date validation
• Track application status
• View leave history

📅 **Date Restrictions:**
• EL: ±30 days window, minimum 3 days
• SL: Past dates only, maximum 15 days before
• CL: ±30 days window, maximum 2 consecutive days

🛠️ **Actions You Can Take:**
• "What's the EL policy according to company rules?"
• "Apply for SL yesterday for medical appointment"
• "Apply EL for 3 days vacation next week"
• "When can I apply for CL?"
• "What are the date restrictions for SL?"

**HR Support Channel:**
📧 Email: hr@company.com
📞 Phone: +1-555-0123
🕒 Hours: Monday-Friday, 9 AM - 6 PM

💡 **All policy responses are extracted from the official company policy PDF!**"""