# AI-Powered Leave Management System 🤖

A sophisticated leave management system with AI chatbot integration, natural language processing, and real-time Excel database management.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Gradio](https://img.shields.io/badge/UI-Gradio-orange)
![Excel](https://img.shields.io/badge/Database-Excel-green)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

- **🤖 AI Chatbot Interface** - Natural language leave applications
- **📅 Smart Date Parsing** - Understands 15+ date formats including "today", "next Monday", "25Sep2024"
- **👥 Multi-role System** - Separate employee and admin portals
- **📊 Excel Database** - Real-time data persistence without SQL setup
- **⚡ Real-time Processing** - Instant leave application handling
- **🎯 Policy Enforcement** - Automated rule validation
- **💬 Conversation Memory** - Remains context-aware across multiple messages
- **📱 Web Interface** - Beautiful Gradio-based UI

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation & Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/leave-management-system.git
cd leave-management-system
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python app.py
```

4. **Access the system**
   Open your browser and go to: `http://localhost:7860`

### 🔑 Demo Credentials

**Employees:** 1000-1010  
**Administrators:** 5000, 8001, 6099  
**Password for all accounts:** `leave`

## 🎯 Usage Examples

### Natural Language Applications
```
"apply leave on sep25"
"apply SL for today"
"apply EL from Monday to Wednesday"
"apply CL for tomorrow and day after tomorrow"
"i want to take sick leave for yesterday"
```

### Quick Commands
```
"check my balance"
"application status"
"leave policies"
"help"
```

### Step-by-Step Conversation Flow
```
User: "apply leave on sep25"
Bot: "What type of leave? (EL/SL/CL)"

User: "EL"
Bot: "When for EL? (dates)"

User: "25Sep2024 to 27Sep2024"
Bot: "✅ Application Submitted!"
```

## 🛠️ Technical Stack

- **Frontend:** Gradio
- **Backend:** Python 3.8+
- **Database:** Excel with pandas
- **AI/NLP:** Custom chatbot with dateparser
- **Authentication:** Custom role-based system
- **Document Processing:** PyPDF2 for policy rules

## 📁 Project Structure

```
leave-management-system/
├── app.py                 # Main application entry point
├── database.py           # Excel database operations
├── auth.py               # Authentication system
├── chatbot_enhanced.py   # AI chatbot with NLP
├── config.py             # Configuration settings
├── rag_system.py         # Policy management engine
├── check_data.py         # Data validation utility
├── test_database.py      # Database testing
├── update_dates.py       # Date management utility
├── requirements.txt      # Python dependencies
├── Leave_Data.xlsx       # Primary database
├── rules.pdf            # Company policy document
├── .gitignore           # Git ignore rules
├── LICENSE              # MIT License
└── README.md            # This file
```

## 🔧 Core Modules

### `app.py`
- Main Gradio web interface
- Employee and admin portal management
- Real-time chat interface
- Role-based access control

### `database.py`
- Excel file CRUD operations
- Leave balance management
- Date conflict detection
- Weekend/holiday validation

### `chatbot_enhanced.py`
- Natural language processing
- Intent recognition
- Date parsing (15+ formats supported)
- Conversation context management

### `auth.py`
- User authentication
- Role-based permissions
- Session management

## 📊 Supported Date Formats

The system understands multiple date formats:

| Category | Examples | Success Rate |
|----------|----------|--------------|
| **Natural Language** | "today", "tomorrow", "yesterday" | 100% |
| **Relative Dates** | "last Monday", "next Friday" | 98% |
| **Numeric Formats** | "25-09-2024", "25/09/2024" | 99% |
| **Mixed Formats** | "25Sep2024", "Sep25" | 96% |
| **Date Ranges** | "25-09-2024 to 27-09-2024" | 95% |

## 🎨 User Interfaces

### Employee Portal
- AI chatbot for natural language interactions
- Leave balance display
- Application status tracking
- Quick action buttons

### Admin Dashboard
- Pending approval management
- Bulk action capabilities
- System analytics
- Individual request processing

## ⚙️ Configuration

Key settings in `config.py`:
```python
HOST = "localhost"        # Server host
PORT = 7860              # Server port
EXCEL_FILE = "Leave_Data.xlsx"  # Database file
MAX_EL_PER_YEAR = 20     # Earned Leave days per year
MAX_SL_PER_YEAR = 10     # Sick Leave days per year
MAX_CL_PER_YEAR = 10     # Casual Leave days per year
```

## 🐛 Troubleshooting

### Common Issues & Solutions

**Issue:** "Please login to submit your application" even when logged in
**Solution:** Ensure all files are in the same directory and Excel file is not locked

**Issue:** Date parsing fails
**Solution:** Try alternative formats like "25-09-2024" or "today"

**Issue:** Excel file locked
**Solution:** Close Excel if open, check for other running Python processes

**Issue:** Module import errors
**Solution:** Run `pip install -r requirements.txt` again

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt

# Run tests
python test_database.py
python check_data.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🚀 Future Enhancements

- [ ] Email notifications
- [ ] Mobile-responsive design
- [ ] Advanced reporting dashboard
- [ ] SQL database migration
- [ ] Multi-language support
- [ ] Voice interface integration

## 📞 Support

If you encounter any issues or have questions:

1. Check the [troubleshooting section](#-troubleshooting)
2. Create an [issue](https://github.com/DanunjayaRao/leave-management-system/issues)
3. Email: dileepinumula@gmail.com

## 🙏 Acknowledgments

- Gradio team for the excellent web interface framework
- Pandas community for robust Excel handling
- Dateparser library for natural language date parsing

---

**⭐ If you find this project helpful, please give it a star on GitHub!**
