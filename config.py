import os

class Config:
    # Application Settings
    DEBUG = True
    HOST = "localhost"  
    PORT = 7860
    
    # File Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    EXCEL_FILE = os.path.join(BASE_DIR, "Leave_Data.xlsx")
    PDF_FILE = os.path.join(BASE_DIR, "rules.pdf")
    
    # Leave Policy from PDF
    MAX_EL_PER_YEAR = 20  # From PDF
    MAX_SL_PER_YEAR = 10  # From PDF  
    MAX_CL_PER_YEAR = 10  # From PDF
    MIN_SERVICE_MONTHS = 3  # 3 months service required
    MIN_EL_DAYS = 3  # Minimum 3 consecutive days for EL
    MAX_CARRY_FORWARD = 10  # Max carry forward days
    LEAVE_NOTICE_DAYS = 7  # 1 week advance notice for planned leave
    
    # Public Holidays 2024-2025 (you can update this list)
    PUBLIC_HOLIDAYS = [
        "2024-01-01", "2024-01-26", "2024-03-25", "2024-03-29", "2024-04-11",
        "2024-05-01", "2024-06-17", "2024-07-17", "2024-08-15", "2024-09-02",
        "2024-10-02", "2024-10-12", "2024-11-01", "2024-12-25",
        "2025-01-01", "2025-01-26", "2025-03-14", "2025-03-29", "2025-04-14",
        "2025-05-01", "2025-06-06", "2025-07-17", "2025-08-15", "2025-10-02",
        "2025-10-20", "2025-11-05", "2025-12-25"
    ]