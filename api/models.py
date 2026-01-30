from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Enum, DECIMAL, CheckConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from .database import Base

class TransactionType(enum.Enum):
    RECEIVED = "received"
    SENT = "sent"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    PAYMENT = "payment"
    AIRTIME = "airtime"
    BILL_PAYMENT = "bill_payment"
    CASH_POWER = "cash_power"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=False, comment="User's phone number")
    full_name = Column(String(100), nullable=True, comment="User's full name")
    account_number = Column(String(50), unique=True, nullable=True, comment="Mobile money account number")
    is_active = Column(Boolean, default=True, comment="Whether the user account is active")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Account creation timestamp")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="Last update timestamp")
    
    # Relationships
    sent_transactions = relationship("SMSRecord", foreign_keys="SMSRecord.sender_id", back_populates="sender")
    received_transactions = relationship("SMSRecord", foreign_keys="SMSRecord.receiver_id", back_populates="receiver")
    
    __table_args__ = (
        CheckConstraint('LENGTH(phone_number) >= 10', name='check_phone_length'),
        CheckConstraint('phone_number LIKE "+%" OR phone_number LIKE "250%"', name='check_phone_format'),
    )

class SMSRecord(Base):
    __tablename__ = "sms_records"
    
    id = Column(Integer, primary_key=True, index=True)
    xml_id = Column(String(100), unique=True, index=True, comment="Original XML ID if exists")
    protocol = Column(Integer, default=0, comment="SMS protocol")
    address = Column(String(100), nullable=False, comment="Sender address (M-Money)")
    body = Column(Text, nullable=False, comment="Full SMS body text")
    date = Column(DateTime, nullable=False, index=True, comment="Original SMS timestamp")
    type = Column(Integer, default=1, comment="SMS type (1=received)")
    service_center = Column(String(50), comment="Service center number")
    readable_date = Column(String(50), comment="Human-readable date")
    contact_name = Column(String(100), default="(Unknown)", comment="Contact name from phone")
    
    # Parsed transaction data
    transaction_type = Column(Enum(TransactionType), nullable=True, index=True, comment="Parsed transaction type")
    amount = Column(DECIMAL(12, 2), nullable=True, comment="Transaction amount in RWF")
    fee = Column(DECIMAL(12, 2), default=0.0, comment="Transaction fee")
    balance_after = Column(DECIMAL(12, 2), nullable=True, comment="Balance after transaction")
    transaction_id = Column(String(50), unique=True, index=True, comment="Financial Transaction Id")
    external_transaction_id = Column(String(50), nullable=True, comment="External Transaction Id")
    transaction_date = Column(DateTime, nullable=True, index=True, comment="Parsed transaction datetime")
    sender_name = Column(String(100), nullable=True, comment="Parsed sender name")
    receiver_name = Column(String(100), nullable=True, comment="Parsed receiver name")
    sender_phone = Column(String(20), nullable=True, comment="Parsed sender phone (masked)")
    receiver_phone = Column(String(20), nullable=True, comment="Parsed receiver phone")
    agent_name = Column(String(100), nullable=True, comment="Agent name for withdrawals")
    agent_phone = Column(String(20), nullable=True, comment="Agent phone number")
    message = Column(Text, nullable=True, comment="Message from sender/receiver")
    token = Column(String(100), nullable=True, comment="Token for bill payments")
    
    # Foreign keys to users
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # System metadata
    is_parsed = Column(Boolean, default=False, comment="Whether SMS has been parsed")
    parse_errors = Column(Text, nullable=True, comment="Any parsing errors encountered")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Record creation timestamp")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="Last update timestamp")
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_transactions")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_transactions")
    categories = relationship("TransactionCategory", secondary="sms_category_association", back_populates="sms_records")
    
    __table_args__ = (
        CheckConstraint('amount >= 0', name='check_amount_positive'),
        CheckConstraint('fee >= 0', name='check_fee_positive'),
        Index('idx_transaction_date_type', 'transaction_date', 'transaction_type'),
        Index('idx_amount_type', 'amount', 'transaction_type'),
    )

class TransactionCategory(Base):
    __tablename__ = "transaction_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, comment="Category name")
    description = Column(Text, nullable=True, comment="Category description")
    code = Column(String(10), unique=True, nullable=False, comment="Short code for category")
    
    # Relationships
    sms_records = relationship("SMSRecord", secondary="sms_category_association", back_populates="categories")
    
    __table_args__ = (
        CheckConstraint('LENGTH(code) <= 10', name='check_code_length'),
    )

class SMS_Category_Association(Base):
    __tablename__ = "sms_category_association"
    
    sms_id = Column(Integer, ForeignKey("sms_records.id", ondelete="CASCADE"), primary_key=True)
    category_id = Column(Integer, ForeignKey("transaction_categories.id", ondelete="CASCADE"), primary_key=True)

class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False, index=True, comment="Log level (INFO, WARNING, ERROR)")
    module = Column(String(100), nullable=False, comment="Module/component name")
    message = Column(Text, nullable=False, comment="Log message")
    details = Column(Text, nullable=True, comment="Additional details or stack trace")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Log creation timestamp")
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        CheckConstraint("level IN ('INFO', 'WARNING', 'ERROR', 'DEBUG', 'CRITICAL')", name='check_log_level'),
        Index('idx_created_at_level', 'created_at', 'level'),
    )

class OTPRecord(Base):
    __tablename__ = "otp_records"
    
    id = Column(Integer, primary_key=True, index=True)
    otp_code = Column(String(10), nullable=False, comment="OTP code")
    phone_number = Column(String(20), nullable=False, comment="Phone number OTP was sent to")
    purpose = Column(String(50), nullable=True, comment="Purpose of OTP")
    is_used = Column(Boolean, default=False, comment="Whether OTP has been used")
    expires_at = Column(DateTime, nullable=False, comment="OTP expiration timestamp")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Creation timestamp")
    
    __table_args__ = (
        CheckConstraint('LENGTH(otp_code) BETWEEN 4 AND 6', name='check_otp_length'),
        Index('idx_phone_expires', 'phone_number', 'expires_at'),
    )