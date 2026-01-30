from pydantic import BaseModel, Field, validator, constr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from decimal import Decimal

class TransactionTypeEnum(str, Enum):
    RECEIVED = "received"
    SENT = "sent"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    PAYMENT = "payment"
    AIRTIME = "airtime"
    BILL_PAYMENT = "bill_payment"
    CASH_POWER = "cash_power"

class UserBase(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=20)
    full_name: Optional[str] = Field(None, max_length=100)
    account_number: Optional[str] = Field(None, max_length=50)
    is_active: bool = True

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    account_number: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class SMSRecordBase(BaseModel):
    address: str
    body: str
    date: datetime
    readable_date: str
    service_center: Optional[str] = None

class SMSRecordCreate(SMSRecordBase):
    protocol: int = 0
    type: int = 1
    contact_name: str = "(Unknown)"

class SMSRecordUpdate(BaseModel):
    transaction_type: Optional[TransactionTypeEnum] = None
    amount: Optional[Decimal] = None
    fee: Optional[Decimal] = None
    balance_after: Optional[Decimal] = None
    transaction_id: Optional[str] = None
    sender_name: Optional[str] = None
    receiver_name: Optional[str] = None
    is_parsed: Optional[bool] = None

class SMSRecord(SMSRecordBase):
    id: int
    protocol: int
    type: int
    contact_name: str
    transaction_type: Optional[TransactionTypeEnum] = None
    amount: Optional[Decimal] = None
    fee: Decimal = Decimal('0.0')
    balance_after: Optional[Decimal] = None
    transaction_id: Optional[str] = None
    external_transaction_id: Optional[str] = None
    transaction_date: Optional[datetime] = None
    sender_name: Optional[str] = None
    receiver_name: Optional[str] = None
    sender_phone: Optional[str] = None
    receiver_phone: Optional[str] = None
    agent_name: Optional[str] = None
    agent_phone: Optional[str] = None
    message: Optional[str] = None
    token: Optional[str] = None
    is_parsed: bool = False
    parse_errors: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Foreign keys
    sender_id: Optional[int] = None
    receiver_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class TransactionCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    code: str

class TransactionCategoryCreate(TransactionCategoryBase):
    pass

class TransactionCategory(TransactionCategoryBase):
    id: int
    
    class Config:
        from_attributes = True

class SystemLogBase(BaseModel):
    level: str
    module: str
    message: str
    details: Optional[str] = None

class SystemLogCreate(SystemLogBase):
    user_id: Optional[int] = None

class SystemLog(SystemLogBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class OTPRecordBase(BaseModel):
    otp_code: str
    phone_number: str
    purpose: Optional[str] = None

class OTPRecordCreate(OTPRecordBase):
    expires_at: datetime

class OTPRecord(OTPRecordBase):
    id: int
    is_used: bool
    expires_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

# Complex JSON models for API responses
class CompleteTransaction(BaseModel):
    """Complete transaction with all related data"""
    sms_record: SMSRecord
    sender: Optional[User] = None
    receiver: Optional[User] = None
    categories: List[TransactionCategory] = []
    logs: List[SystemLog] = []
    
    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_transactions: int
    total_amount: Decimal
    average_transaction: Decimal
    transaction_counts: Dict[str, int]
    daily_volume: List[Dict[str, Any]]
    top_senders: List[Dict[str, Any]]
    top_receivers: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    
    class Config:
        from_attributes = True

# Request/Response models for authentication
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str