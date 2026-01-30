"""
MoMo SMS Analytics API Package
Team Eight: James Giir Deng & Byusa M Martin De Poles
"""

__version__ = "1.0.0"
__author__ = "Team Eight"
__email__ = "team8@alustudent.com"

from .database import Base, engine, SessionLocal, get_db
from .models import (
    User, 
    SMSRecord, 
    TransactionCategory, 
    SystemLog, 
    OTPRecord,
    TransactionType
)
from .schemas import (
    UserCreate, 
    UserUpdate, 
    User,
    SMSRecordCreate, 
    SMSRecordUpdate, 
    SMSRecord,
    CompleteTransaction,
    DashboardStats
)
from .crud import (
    get_user, 
    create_user, 
    get_sms_record,
    create_sms_record,
    get_dashboard_stats
)
from .parse_xml import parse_xml_file, process_xml_file
from .auth import verify_password, get_password_hash, create_access_token

__all__ = [
    # Database
    "Base", "engine", "SessionLocal", "get_db",
    
    # Models
    "User", "SMSRecord", "TransactionCategory", "SystemLog", "OTPRecord", "TransactionType",
    
    # Schemas
    "UserCreate", "UserUpdate", "User",
    "SMSRecordCreate", "SMSRecordUpdate", "SMSRecord",
    "CompleteTransaction", "DashboardStats",
    
    # CRUD operations
    "get_user", "create_user", "get_sms_record", "create_sms_record", "get_dashboard_stats",
    
    # XML Parsing
    "parse_xml_file", "process_xml_file",
    
    # Authentication
    "verify_password", "get_password_hash", "create_access_token",
]