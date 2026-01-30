"""
SQLAlchemy models for the MoMo SMS Analytics System
Team Eight: James Giir Deng & Byusa M Martin De Poles
"""
from sqlalchemy import (
    Column, Integer, String, DateTime, Float, Boolean, Text, 
    ForeignKey, Enum, DECIMAL, CheckConstraint, Index, 
    JSON, LargeBinary, func, UniqueConstraint, text
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import expression
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.dialects.mysql import ENUM as MySQLEnum
from datetime import datetime, timezone
import enum
import re
import logging
from typing import Optional, List
from decimal import Decimal

from .database import Base

logger = logging.getLogger(__name__)

class TransactionType(enum.Enum):
    """Enumeration of possible transaction types"""
    RECEIVED = "received"
    SENT = "sent"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    PAYMENT = "payment"
    AIRTIME = "airtime"
    BILL_PAYMENT = "bill_payment"
    CASH_POWER = "cash_power"
    COMMISSION = "commission"
    REFUND = "refund"
    SALARY = "salary"
    UNKNOWN = "unknown"

class LogLevel(enum.Enum):
    """Enumeration of log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class User(Base):
    """
    User entity representing customers, senders, and receivers
    
    Stores user information for transaction tracking and analytics
    """
    __tablename__ = "users"
    
    # Primary key and identification
    id = Column(Integer, primary_key=True, index=True, autoincrement=True,
                comment="Unique identifier for the user")
    uuid = Column(String(36), unique=True, index=True, nullable=False,
                  server_default=text("UUID()"),
                  comment="Universally unique identifier for the user")
    
    # Contact information
    phone_number = Column(String(20), unique=True, index=True, nullable=False,
                          comment="User's phone number in E.164 format")
    email = Column(String(255), unique=True, index=True, nullable=True,
                   comment="User's email address")
    full_name = Column(String(100), nullable=True,
                       comment="User's full name")
    account_number = Column(String(50), unique=True, nullable=True,
                            comment="Mobile money account number")
    
    # Account information
    account_type = Column(String(20), default="personal",
                          comment="Account type: personal, business, agent")
    is_active = Column(Boolean, default=True,
                       comment="Whether the user account is active")
    is_verified = Column(Boolean, default=False,
                         comment="Whether the user has been verified")
    verification_date = Column(DateTime, nullable=True,
                               comment="Date when user was verified")
    
    # Security
    password_hash = Column(String(255), nullable=True,
                           comment="Hashed password for user authentication")
    last_login = Column(DateTime, nullable=True,
                        comment="Last login timestamp")
    login_attempts = Column(Integer, default=0,
                            comment="Number of failed login attempts")
    locked_until = Column(DateTime, nullable=True,
                          comment="Account lock expiration time")
    
    # Preferences
    language = Column(String(10), default="en",
                      comment="User's preferred language")
    timezone = Column(String(50), default="UTC",
                      comment="User's timezone")
    notification_preferences = Column(JSON, default=dict,
                                      comment="User's notification preferences")
    
    # Metadata
    created_at = Column(DateTime(timezone=True), 
                        server_default=func.now(),
                        nullable=False,
                        comment="Account creation timestamp")
    updated_at = Column(DateTime(timezone=True), 
                        server_default=func.now(),
                        onupdate=func.now(),
                        nullable=False,
                        comment="Last update timestamp")
    deleted_at = Column(DateTime(timezone=True), nullable=True,
                        comment="Soft delete timestamp")
    
    # Relationships
    sent_transactions = relationship(
        "SMSRecord", 
        foreign_keys="SMSRecord.sender_id", 
        back_populates="sender",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    received_transactions = relationship(
        "SMSRecord", 
        foreign_keys="SMSRecord.receiver_id", 
        back_populates="receiver",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    logs = relationship(
        "SystemLog",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    
    # Table arguments including constraints and indexes
    __table_args__ = (
        # Check constraints
        CheckConstraint('LENGTH(phone_number) >= 10', name='check_phone_length'),
        CheckConstraint('phone_number LIKE "+%" OR phone_number LIKE "250%"', 
                       name='check_phone_format'),
        CheckConstraint('email IS NULL OR email LIKE "%@%.%"', 
                       name='check_email_format'),
        CheckConstraint('account_type IN ("personal", "business", "agent")', 
                       name='check_account_type'),
        
        # Indexes for performance
        Index('idx_users_phone_active', 'phone_number', 'is_active'),
        Index('idx_users_created_at', 'created_at'),
        Index('idx_users_updated_at', 'updated_at'),
        Index('idx_users_deleted_at', 'deleted_at'),
        
        # Comment
        {'comment': 'Stores user information for senders and receivers'},
    )
    
    @validates('phone_number')
    def validate_phone_number(self, key, phone_number):
        """Validate phone number format"""
        if not re.match(r'^\+?\d{10,15}$', phone_number):
            raise ValueError("Invalid phone number format")
        return phone_number
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format if provided"""
        if email is not None:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                raise ValueError("Invalid email format")
        return email
    
    @hybrid_property
    def total_transactions(self):
        """Calculate total number of transactions for this user"""
        return len(self.sent_transactions.all()) + len(self.received_transactions.all())
    
    @hybrid_property
    def total_sent(self):
        """Calculate total amount sent by this user"""
        sent_amounts = [t.amount or 0 for t in self.sent_transactions.all()]
        return sum(sent_amounts)
    
    @hybrid_property
    def total_received(self):
        """Calculate total amount received by this user"""
        received_amounts = [t.amount or 0 for t in self.received_transactions.all()]
        return sum(received_amounts)
    
    @hybrid_property
    def net_flow(self):
        """Calculate net flow (received - sent)"""
        return self.total_received - self.total_sent
    
    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'phone_number': self.phone_number,
            'email': self.email,
            'full_name': self.full_name,
            'account_number': self.account_number,
            'account_type': self.account_type,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'total_transactions': self.total_transactions,
            'total_sent': float(self.total_sent) if self.total_sent else 0,
            'total_received': float(self.total_received) if self.total_received else 0,
            'net_flow': float(self.net_flow) if self.net_flow else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<User(id={self.id}, phone='{self.phone_number}', name='{self.full_name}')>"


class SMSRecord(Base):
    """
    SMS Record entity representing raw SMS data and parsed transactions
    
    This is the core entity storing both raw SMS messages and parsed
    transaction information
    """
    __tablename__ = "sms_records"
    
    # Primary key and identification
    id = Column(Integer, primary_key=True, index=True, autoincrement=True,
                comment="Unique identifier for the SMS record")
    uuid = Column(String(36), unique=True, index=True, nullable=False,
                  server_default=text("UUID()"),
                  comment="Universally unique identifier for the SMS")
    
    # Original SMS data
    xml_id = Column(String(100), unique=True, index=True, nullable=True,
                    comment="Original XML ID from SMS backup")
    protocol = Column(Integer, default=0,
                      comment="SMS protocol (0=SMS, 1=MMS)")
    address = Column(String(100), nullable=False, index=True,
                     comment="Sender address (usually 'M-Money')")
    body = Column(Text, nullable=False,
                  comment="Full SMS body text")
    date = Column(DateTime, nullable=False, index=True,
                  comment="Original SMS timestamp from device")
    type = Column(Integer, default=1,
                  comment="SMS type (1=received, 2=sent)")
    subject = Column(String(255), nullable=True,
                     comment="SMS subject (usually null)")
    toa = Column(String(50), nullable=True,
                 comment="Type of Address")
    sc_toa = Column(String(50), nullable=True,
                    comment="Service Center Type of Address")
    service_center = Column(String(50), nullable=True, index=True,
                            comment="Service center number")
    read = Column(Integer, default=1,
                  comment="Whether SMS was read (0=unread, 1=read)")
    status = Column(Integer, default=-1,
                    comment="SMS status")
    locked = Column(Integer, default=0,
                    comment="Whether SMS is locked")
    date_sent = Column(DateTime, nullable=True,
                       comment="Date when SMS was sent")
    sub_id = Column(Integer, nullable=True,
                    comment="Subscription ID")
    readable_date = Column(String(50), nullable=True,
                           comment="Human-readable date from SMS")
    contact_name = Column(String(100), default="(Unknown)",
                          comment="Contact name from phone book")
    
    # Parsed transaction data
    transaction_type = Column(
        Enum(TransactionType), 
        nullable=True, 
        index=True,
        comment="Parsed transaction type"
    )
    amount = Column(DECIMAL(12, 2), nullable=True, index=True,
                    comment="Transaction amount in RWF")
    currency = Column(String(3), default="RWF",
                      comment="Transaction currency (default: RWF)")
    fee = Column(DECIMAL(12, 2), default=Decimal('0.00'),
                 comment="Transaction fee")
    balance_before = Column(DECIMAL(12, 2), nullable=True,
                            comment="Balance before transaction")
    balance_after = Column(DECIMAL(12, 2), nullable=True, index=True,
                           comment="Balance after transaction")
    transaction_id = Column(String(50), unique=True, index=True,
                            comment="Financial Transaction Id from provider")
    external_transaction_id = Column(String(50), nullable=True, index=True,
                                     comment="External Transaction Id")
    transaction_date = Column(DateTime, nullable=True, index=True,
                              comment="Parsed transaction datetime from SMS")
    
    # Party information
    sender_name = Column(String(100), nullable=True, index=True,
                         comment="Parsed sender name from SMS")
    receiver_name = Column(String(100), nullable=True, index=True,
                           comment="Parsed receiver name from SMS")
    sender_phone = Column(String(20), nullable=True, index=True,
                          comment="Parsed sender phone (may be masked)")
    receiver_phone = Column(String(20), nullable=True, index=True,
                            comment="Parsed receiver phone")
    agent_name = Column(String(100), nullable=True,
                        comment="Agent name for withdrawals/deposits")
    agent_phone = Column(String(20), nullable=True,
                         comment="Agent phone number")
    
    # Additional transaction details
    message = Column(Text, nullable=True,
                     comment="Message from sender/receiver")
    token = Column(String(100), nullable=True,
                   comment="Token for bill payments (electricity, etc.)")
    reference_number = Column(String(50), nullable=True,
                              comment="Reference number for the transaction")
    location = Column(String(255), nullable=True,
                      comment="Transaction location/agent location")
    device_id = Column(String(100), nullable=True,
                       comment="Device ID from which SMS originated")
    
    # Foreign keys to users
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), 
                       nullable=True, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), 
                         nullable=True, index=True)
    agent_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), 
                      nullable=True, index=True)
    
    # System metadata
    is_parsed = Column(Boolean, default=False, index=True,
                       comment="Whether SMS has been successfully parsed")
    is_valid = Column(Boolean, default=True, index=True,
                      comment="Whether SMS is valid and should be processed")
    parse_errors = Column(Text, nullable=True,
                          comment="Any parsing errors encountered")
    parsing_duration = Column(Float, nullable=True,
                              comment="Time taken to parse SMS in seconds")
    parsed_by = Column(String(50), default="system",
                       comment="System/User that parsed this SMS")
    confidence_score = Column(Float, default=1.0,
                              comment="Confidence score for parsing accuracy (0-1)")
    
    # Audit and timestamps
    created_at = Column(DateTime(timezone=True), 
                        server_default=func.now(),
                        nullable=False,
                        comment="Record creation timestamp")
    updated_at = Column(DateTime(timezone=True), 
                        server_default=func.now(),
                        onupdate=func.now(),
                        nullable=False,
                        comment="Last update timestamp")
    parsed_at = Column(DateTime(timezone=True), nullable=True,
                       comment="Timestamp when SMS was parsed")
    processed_at = Column(DateTime(timezone=True), nullable=True,
                          comment="Timestamp when SMS was processed")
    
    # Relationships
    sender = relationship(
        "User", 
        foreign_keys=[sender_id], 
        back_populates="sent_transactions",
        lazy="joined"
    )
    receiver = relationship(
        "User", 
        foreign_keys=[receiver_id], 
        back_populates="received_transactions",
        lazy="joined"
    )
    agent = relationship(
        "User", 
        foreign_keys=[agent_id],
        lazy="joined"
    )
    categories = relationship(
        "TransactionCategory", 
        secondary="sms_category_association",
        back_populates="sms_records",
        lazy="joined",
        cascade="all, delete"
    )
    
    # Table arguments including constraints and indexes
    __table_args__ = (
        # Check constraints
        CheckConstraint('amount >= 0', name='check_amount_positive'),
        CheckConstraint('fee >= 0', name='check_fee_positive'),
        CheckConstraint('balance_after >= 0', name='check_balance_positive'),
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', 
                       name='check_confidence_score'),
        CheckConstraint('type IN (1, 2)', name='check_sms_type'),
        
        # Composite indexes for common queries
        Index('idx_transaction_date_type', 'transaction_date', 'transaction_type'),
        Index('idx_amount_type', 'amount', 'transaction_type'),
        Index('idx_sender_receiver_date', 'sender_id', 'receiver_id', 'transaction_date'),
        Index('idx_parsed_valid', 'is_parsed', 'is_valid'),
        Index('idx_date_range', 'transaction_date', 'created_at'),
        Index('idx_search', 'sender_name', 'receiver_name', 'transaction_id'),
        Index('idx_body_search', 'body', mysql_prefix='FULLTEXT'),
        
        # Unique constraints
        UniqueConstraint('transaction_id', name='uq_transaction_id'),
        UniqueConstraint('xml_id', name='uq_xml_id'),
        UniqueConstraint('uuid', name='uq_sms_uuid'),
        
        # Comment
        {'comment': 'Stores raw SMS records and parsed transaction data'},
    )
    
    @validates('amount', 'fee', 'balance_after')
    def validate_monetary_values(self, key, value):
        """Validate monetary values are non-negative"""
        if value is not None and value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value
    
    @validates('transaction_type')
    def validate_transaction_type(self, key, transaction_type):
        """Validate transaction type"""
        if transaction_type not in TransactionType:
            raise ValueError(f"Invalid transaction type: {transaction_type}")
        return transaction_type
    
    @hybrid_property
    def net_amount(self):
        """Calculate net amount (amount - fee)"""
        if self.amount is None:
            return None
        fee = self.fee or Decimal('0.00')
        return self.amount - fee
    
    @hybrid_property
    def is_incoming(self):
        """Check if transaction is incoming (received/deposit)"""
        return self.transaction_type in [
            TransactionType.RECEIVED, 
            TransactionType.DEPOSIT,
            TransactionType.REFUND,
            TransactionType.SALARY
        ]
    
    @hybrid_property
    def is_outgoing(self):
        """Check if transaction is outgoing (sent/withdrawal/payment)"""
        return self.transaction_type in [
            TransactionType.SENT,
            TransactionType.WITHDRAWAL,
            TransactionType.PAYMENT,
            TransactionType.AIRTIME,
            TransactionType.BILL_PAYMENT,
            TransactionType.CASH_POWER,
            TransactionType.COMMISSION
        ]
    
    @hybrid_property
    def days_since_transaction(self):
        """Calculate days since transaction"""
        if not self.transaction_date:
            return None
        delta = datetime.now(timezone.utc) - self.transaction_date
        return delta.days
    
    @hybrid_method
    def matches_pattern(self, pattern):
        """Check if SMS body matches a regex pattern"""
        import re
        return re.search(pattern, self.body or '') is not None
    
    def to_dict(self, include_related=True):
        """Convert SMS record to dictionary"""
        result = {
            'id': self.id,
            'uuid': self.uuid,
            'address': self.address,
            'body': self.body,
            'date': self.date.isoformat() if self.date else None,
            'readable_date': self.readable_date,
            'transaction_type': self.transaction_type.value if self.transaction_type else None,
            'amount': float(self.amount) if self.amount else None,
            'currency': self.currency,
            'fee': float(self.fee) if self.fee else 0.0,
            'balance_after': float(self.balance_after) if self.balance_after else None,
            'transaction_id': self.transaction_id,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'sender_name': self.sender_name,
            'receiver_name': self.receiver_name,
            'sender_phone': self.sender_phone,
            'receiver_phone': self.receiver_phone,
            'is_parsed': self.is_parsed,
            'is_valid': self.is_valid,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'categories': [cat.code for cat in self.categories] if self.categories else [],
        }
        
        if include_related and self.sender:
            result['sender'] = self.sender.to_dict()
        if include_related and self.receiver:
            result['receiver'] = self.receiver.to_dict()
        
        return result
    
    def __repr__(self):
        return f"<SMSRecord(id={self.id}, type={self.transaction_type}, amount={self.amount})>"


class TransactionCategory(Base):
    """
    Transaction Category entity for classifying transactions
    
    Supports hierarchical categorization and flexible tagging
    """
    __tablename__ = "transaction_categories"
    
    # Primary key and identification
    id = Column(Integer, primary_key=True, index=True, autoincrement=True,
                comment="Unique identifier for the category")
    uuid = Column(String(36), unique=True, index=True, nullable=False,
                  server_default=text("UUID()"),
                  comment="Universally unique identifier for the category")
    
    # Category information
    name = Column(String(50), unique=True, nullable=False, index=True,
                  comment="Category name (e.g., 'Money Transfer')")
    description = Column(Text, nullable=True,
                         comment="Category description")
    code = Column(String(10), unique=True, nullable=False, index=True,
                  comment="Short code for category (e.g., 'TRANSFER')")
    
    # Hierarchical categorization
    parent_id = Column(Integer, ForeignKey("transaction_categories.id", ondelete="SET NULL"), 
                       nullable=True, index=True)
    level = Column(Integer, default=0,
                   comment="Hierarchy level (0=root, 1=child, etc.)")
    path = Column(String(255), nullable=True,
                  comment="Path in category tree (e.g., '1.3.5')")
    
    # Metadata
    is_active = Column(Boolean, default=True,
                       comment="Whether category is active")
    icon = Column(String(50), nullable=True,
                  comment="Icon name for UI display")
    color = Column(String(7), nullable=True,
                   comment="Hex color code for UI (#RRGGBB)")
    metadata = Column(JSON, default=dict,
                      comment="Additional metadata for the category")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), 
                        server_default=func.now(),
                        nullable=False,
                        comment="Category creation timestamp")
    updated_at = Column(DateTime(timezone=True), 
                        server_default=func.now(),
                        onupdate=func.now(),
                        nullable=False,
                        comment="Last update timestamp")
    
    # Relationships
    parent = relationship(
        "TransactionCategory", 
        remote_side=[id],
        backref="children",
        lazy="joined"
    )
    sms_records = relationship(
        "SMSRecord", 
        secondary="sms_category_association",
        back_populates="categories",
        lazy="dynamic",
        cascade="all, delete"
    )
    
    # Table arguments
    __table_args__ = (
        # Check constraints
        CheckConstraint('LENGTH(code) BETWEEN 2 AND 10', name='check_code_length'),
        CheckConstraint('LENGTH(name) BETWEEN 2 AND 50', name='check_name_length'),
        CheckConstraint('level >= 0', name='check_level_positive'),
        
        # Indexes
        Index('idx_category_parent', 'parent_id', 'is_active'),
        Index('idx_category_level', 'level', 'is_active'),
        Index('idx_category_path', 'path'),
        
        # Comment
        {'comment': 'Categories for transaction types (transfer, deposit, payment, etc.)'},
    )
    
    @validates('code')
    def validate_code(self, key, code):
        """Validate category code format"""
        if not re.match(r'^[A-Z_]{2,10}$', code):
            raise ValueError("Category code must be 2-10 uppercase letters or underscores")
        return code
    
    @validates('color')
    def validate_color(self, key, color):
        """Validate color hex code"""
        if color and not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            raise ValueError("Color must be a hex code (#RRGGBB)")
        return color
    
    @hybrid_property
    def full_path(self):
        """Get full hierarchical path"""
        if self.path and self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    @hybrid_property
    def transaction_count(self):
        """Get number of transactions in this category"""
        return len(self.sms_records.all()) if self.sms_records else 0
    
    def to_dict(self, include_children=True):
        """Convert category to dictionary"""
        result = {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'description': self.description,
            'code': self.code,
            'level': self.level,
            'path': self.path,
            'full_path': self.full_path,
            'is_active': self.is_active,
            'icon': self.icon,
            'color': self.color,
            'transaction_count': self.transaction_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_children and self.children:
            result['children'] = [child.to_dict(include_children=False) for child in self.children]
        
        if self.parent and include_children:
            result['parent'] = {
                'id': self.parent.id,
                'name': self.parent.name,
                'code': self.parent.code
            }
        
        return result
    
    def __repr__(self):
        return f"<TransactionCategory(id={self.id}, code='{self.code}', name='{self.name}')>"


class SMS_Category_Association(Base):
    """
    Junction table for many-to-many relationship between SMS records and categories
    """
    __tablename__ = "sms_category_association"
    
    sms_id = Column(
        Integer, 
        ForeignKey("sms_records.id", ondelete="CASCADE"), 
        primary_key=True,
        comment="Reference to SMS record"
    )
    category_id = Column(
        Integer, 
        ForeignKey("transaction_categories.id", ondelete="CASCADE"), 
        primary_key=True,
        comment="Reference to transaction category"
    )
    assigned_by = Column(
        String(50), 
        nullable=True,
        comment="User/system that assigned this category"
    )
    confidence = Column(
        Float, 
        default=1.0,
        comment="Confidence score for this categorization (0-1)"
    )
    assigned_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when category was assigned"
    )
    
    # Relationships
    sms_record = relationship("SMSRecord", backref="category_associations")
    category = relationship("TransactionCategory", backref="sms_associations")
    
    # Table arguments
    __table_args__ = (
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='check_association_confidence'),
        Index('idx_association_sms', 'sms_id'),
        Index('idx_association_category', 'category_id'),
        Index('idx_association_sms_category', 'sms_id', 'category_id'),
        {'comment': 'Many-to-many relationship between SMS records and categories'},
    )
    
    def to_dict(self):
        """Convert association to dictionary"""
        return {
            'sms_id': self.sms_id,
            'category_id': self.category_id,
            'assigned_by': self.assigned_by,
            'confidence': self.confidence,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
        }


class SystemLog(Base):
    """
    System Log entity for audit trails and error tracking
    
    Comprehensive logging for system events, user actions, and errors
    """
    __tablename__ = "system_logs"
    
    # Primary key and identification
    id = Column(Integer, primary_key=True, index=True, autoincrement=True,
                comment="Unique identifier for the log entry")
    uuid = Column(String(36), unique=True, index=True, nullable=False,
                  server_default=text("UUID()"),
                  comment="Universally unique identifier for the log entry")
    
    # Log information
    level = Column(
        Enum(LogLevel), 
        nullable=False, 
        index=True,
        comment="Log level (INFO, WARNING, ERROR, DEBUG, CRITICAL)"
    )
    module = Column(String(100), nullable=False, index=True,
                    comment="Module/component name (e.g., 'API', 'Parser', 'Database')")
    function = Column(String(100), nullable=True,
                      comment="Function/method name")
    message = Column(Text, nullable=False,
                     comment="Log message")
    details = Column(Text, nullable=True,
                     comment="Additional details or stack trace")
    
    # Context information
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), 
                     nullable=True, index=True)
    ip_address = Column(String(45), nullable=True,
                        comment="IP address of the requester")
    user_agent = Column(String(500), nullable=True,
                        comment="User agent string")
    request_id = Column(String(100), nullable=True, index=True,
                        comment="Request identifier for tracking")
    session_id = Column(String(100), nullable=True,
                        comment="User session identifier")
    
    # Performance metrics
    duration = Column(Float, nullable=True,
                      comment="Duration of the operation in seconds")
    memory_usage = Column(Integer, nullable=True,
                          comment="Memory usage in bytes")
    
    # Error specific fields
    error_code = Column(String(50), nullable=True,
                        comment="Error code if applicable")
    error_type = Column(String(100), nullable=True,
                        comment="Type of error (e.g., 'ValidationError', 'DatabaseError')")
    
    # Metadata
    tags = Column(JSON, default=list,
                  comment="Tags for categorization and filtering")
    metadata = Column(JSON, default=dict,
                      comment="Additional metadata")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), 
                        server_default=func.now(),
                        nullable=False,
                        comment="Log creation timestamp")
    
    # Relationships
    user = relationship("User", back_populates="logs")
    
    # Table arguments
    __table_args__ = (
        # Check constraints
        CheckConstraint('duration >= 0', name='check_duration_positive'),
        CheckConstraint('memory_usage >= 0', name='check_memory_positive'),
        
        # Indexes for common queries
        Index('idx_logs_created_at_level', 'created_at', 'level'),
        Index('idx_logs_module_level', 'module', 'level'),
        Index('idx_logs_user_created', 'user_id', 'created_at'),
        Index('idx_logs_request', 'request_id'),
        Index('idx_logs_error', 'error_code', 'created_at'),
        
        # Comment
        {'comment': 'System logs for audit trails and error tracking'},
    )
    
    @validates('level')
    def validate_level(self, key, level):
        """Validate log level"""
        if isinstance(level, str):
            level = LogLevel(level.upper())
        if level not in LogLevel:
            raise ValueError(f"Invalid log level: {level}")
        return level
    
    @hybrid_property
    def is_error(self):
        """Check if log is an error level"""
        return self.level in [LogLevel.ERROR, LogLevel.CRITICAL]
    
    @hybrid_property
    def is_warning(self):
        """Check if log is a warning level"""
        return self.level == LogLevel.WARNING
    
    def to_dict(self, include_user=True):
        """Convert log entry to dictionary"""
        result = {
            'id': self.id,
            'uuid': self.uuid,
            'level': self.level.value,
            'module': self.module,
            'function': self.function,
            'message': self.message,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'request_id': self.request_id,
            'session_id': self.session_id,
            'duration': self.duration,
            'memory_usage': self.memory_usage,
            'error_code': self.error_code,
            'error_type': self.error_type,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_error': self.is_error,
            'is_warning': self.is_warning,
        }
        
        if include_user and self.user:
            result['user'] = {
                'id': self.user.id,
                'phone_number': self.user.phone_number,
                'full_name': self.user.full_name
            }
        else:
            result['user_id'] = self.user_id
        
        return result
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, level={self.level}, module='{self.module}')>"


class OTPRecord(Base):
    """
    OTP Record entity for one-time password tracking
    
    Secure storage and management of OTPs for authentication and verification
    """
    __tablename__ = "otp_records"
    
    # Primary key and identification
    id = Column(Integer, primary_key=True, index=True, autoincrement=True,
                comment="Unique identifier for the OTP record")
    uuid = Column(String(36), unique=True, index=True, nullable=False,
                  server_default=text("UUID()"),
                  comment="Universally unique identifier for the OTP")
    
    # OTP information
    otp_code = Column(String(10), nullable=False,
                      comment="OTP code (hashed)")
    otp_code_plain = Column(String(10), nullable=True,
                            comment="Plain text OTP code (encrypted)")
    phone_number = Column(String(20), nullable=False, index=True,
                          comment="Phone number OTP was sent to")
    email = Column(String(255), nullable=True, index=True,
                   comment="Email address OTP was sent to")
    
    # Purpose and usage
    purpose = Column(String(50), nullable=False, index=True,
                     comment="Purpose of OTP (e.g., 'login', 'verification', 'reset_password')")
    is_used = Column(Boolean, default=False, index=True,
                     comment="Whether OTP has been used")
    used_at = Column(DateTime, nullable=True,
                     comment="Timestamp when OTP was used")
    attempts = Column(Integer, default=0,
                      comment="Number of verification attempts")
    
    # Security and expiration
    expires_at = Column(DateTime, nullable=False, index=True,
                        comment="OTP expiration timestamp")
    ip_address = Column(String(45), nullable=True,
                        comment="IP address that requested the OTP")
    user_agent = Column(String(500), nullable=True,
                        comment="User agent of the requester")
    
    # Metadata
    metadata = Column(JSON, default=dict,
                      comment="Additional metadata (e.g., user_id, session_id)")
    delivery_method = Column(String(20), default="sms",
                             comment="Delivery method (sms, email, app)")
    delivery_status = Column(String(20), default="pending",
                             comment="Delivery status (pending, sent, failed)")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), 
                        server_default=func.now(),
                        nullable=False,
                        comment="OTP creation timestamp")
    updated_at = Column(DateTime(timezone=True), 
                        server_default=func.now(),
                        onupdate=func.now(),
                        nullable=False,
                        comment="Last update timestamp")
    
    # Table arguments
    __table_args__ = (
        # Check constraints
        CheckConstraint('LENGTH(otp_code) BETWEEN 4 AND 10', name='check_otp_length'),
        CheckConstraint('attempts >= 0', name='check_attempts_positive'),
        CheckConstraint('expires_at > created_at', name='check_expiry_after_creation'),
        CheckConstraint('purpose IN ("login", "verification", "reset_password", "transaction")', 
                       name='check_purpose'),
        CheckConstraint('delivery_method IN ("sms", "email", "app")', name='check_delivery_method'),
        CheckConstraint('delivery_status IN ("pending", "sent", "failed", "delivered")', 
                       name='check_delivery_status'),
        
        # Indexes for performance
        Index('idx_otp_phone_expires', 'phone_number', 'expires_at', 'is_used'),
        Index('idx_otp_email_expires', 'email', 'expires_at', 'is_used'),
        Index('idx_otp_purpose', 'purpose', 'created_at'),
        Index('idx_otp_used', 'is_used', 'created_at'),
        
        # Comment
        {'comment': 'One-time password records for security and authentication'},
    )
    
    @validates('otp_code')
    def validate_otp_code(self, key, otp_code):
        """Validate OTP code format"""
        if not re.match(r'^[0-9]{4,10}$', otp_code):
            raise ValueError("OTP code must be 4-10 digits")
        return otp_code
    
    @validates('phone_number')
    def validate_phone_number(self, key, phone_number):
        """Validate phone number format"""
        if not re.match(r'^\+?\d{10,15}$', phone_number):
            raise ValueError("Invalid phone number format")
        return phone_number
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format if provided"""
        if email is not None:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                raise ValueError("Invalid email format")
        return email
    
    @hybrid_property
    def is_expired(self):
        """Check if OTP is expired"""
        from datetime import datetime
        return datetime.now(timezone.utc) > self.expires_at
    
    @hybrid_property
    def is_valid(self):
        """Check if OTP is valid (not used and not expired)"""
        return not self.is_used and not self.is_expired
    
    @hybrid_property
    def seconds_remaining(self):
        """Get seconds remaining until expiration"""
        from datetime import datetime
        if self.is_expired:
            return 0
        delta = self.expires_at - datetime.now(timezone.utc)
        return int(delta.total_seconds())
    
    def to_dict(self, include_sensitive=False):
        """Convert OTP record to dictionary"""
        result = {
            'id': self.id,
            'uuid': self.uuid,
            'phone_number': self.phone_number,
            'email': self.email,
            'purpose': self.purpose,
            'is_used': self.is_used,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'attempts': self.attempts,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'ip_address': self.ip_address,
            'delivery_method': self.delivery_method,
            'delivery_status': self.delivery_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_expired': self.is_expired,
            'is_valid': self.is_valid,
            'seconds_remaining': self.seconds_remaining,
        }
        
        if include_sensitive:
            result['otp_code'] = self.otp_code_plain
        
        return result
    
    def __repr__(self):
        return f"<OTPRecord(id={self.id}, phone='{self.phone_number}', purpose='{self.purpose}')>"


# Additional helper models
class DashboardCache(Base):
    """
    Dashboard Cache entity for caching expensive dashboard queries
    
    Improves performance by caching dashboard statistics and aggregations
    """
    __tablename__ = "dashboard_cache"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True,
                comment="Unique identifier for the cache entry")
    cache_key = Column(String(100), unique=True, nullable=False, index=True,
                       comment="Unique cache key for the data")
    cache_data = Column(JSON, nullable=False,
                        comment="Cached data in JSON format")
    cache_type = Column(String(50), nullable=False, index=True,
                        comment="Type of cached data (e.g., 'stats', 'chart', 'table')")
    expires_at = Column(DateTime, nullable=False, index=True,
                        comment="Cache expiration timestamp")
    created_at = Column(DateTime(timezone=True), 
                        server_default=func.now(),
                        nullable=False,
                        comment="Cache creation timestamp")
    updated_at = Column(DateTime(timezone=True), 
                        server_default=func.now(),
                        onupdate=func.now(),
                        nullable=False,
                        comment="Last update timestamp")
    
    __table_args__ = (
        Index('idx_cache_expires_type', 'expires_at', 'cache_type'),
        CheckConstraint('expires_at > created_at', name='check_cache_expiry'),
        {'comment': 'Cache for dashboard statistics to improve performance'},
    )
    
    @hybrid_property
    def is_expired(self):
        """Check if cache is expired"""
        from datetime import datetime
        return datetime.now(timezone.utc) > self.expires_at
    
    def to_dict(self):
        """Convert cache entry to dictionary"""
        return {
            'id': self.id,
            'cache_key': self.cache_key,
            'cache_type': self.cache_type,
            'cache_data': self.cache_data,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_expired': self.is_expired,
        }


class APIAccessLog(Base):
    """
    API Access Log entity for tracking API usage
    
    Logs all API requests for monitoring, analytics, and security
    """
    __tablename__ = "api_access_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True,
                comment="Unique identifier for the access log")
    uuid = Column(String(36), unique=True, index=True, nullable=False,
                  server_default=text("UUID()"))
    
    # Request information
    method = Column(String(10), nullable=False, index=True,
                    comment="HTTP method (GET, POST, PUT, DELETE)")
    endpoint = Column(String(255), nullable=False, index=True,
                      comment="API endpoint path")
    query_params = Column(JSON, nullable=True,
                          comment="Query parameters")
    request_body = Column(Text, nullable=True,
                          comment="Request body (truncated if too large)")
    
    # Response information
    status_code = Column(Integer, nullable=False, index=True,
                         comment="HTTP status code")
    response_body = Column(Text, nullable=True,
                           comment="Response body (truncated if too large)")
    response_size = Column(Integer, nullable=True,
                           comment="Response size in bytes")
    
    # User and session information
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), 
                     nullable=True, index=True)
    api_key = Column(String(100), nullable=True, index=True,
                     comment="API key used for authentication")
    session_id = Column(String(100), nullable=True, index=True,
                        comment="User session identifier")
    
    # Network information
    ip_address = Column(String(45), nullable=False, index=True,
                        comment="Client IP address")
    user_agent = Column(String(500), nullable=True,
                        comment="User agent string")
    referer = Column(String(500), nullable=True,
                     comment="HTTP referer header")
    
    # Performance metrics
    duration = Column(Float, nullable=False,
                      comment="Request duration in seconds")
    server = Column(String(100), nullable=True,
                    comment="Server that handled the request")
    
    # Metadata
    tags = Column(JSON, default=list,
                  comment="Tags for categorization")
    metadata = Column(JSON, default=dict,
                      comment="Additional metadata")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), 
                        server_default=func.now(),
                        nullable=False,
                        comment="Request timestamp")
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        CheckConstraint('duration >= 0', name='check_duration_positive'),
        CheckConstraint('response_size >= 0', name='check_response_size_positive'),
        Index('idx_access_user_date', 'user_id', 'created_at'),
        Index('idx_access_endpoint_date', 'endpoint', 'created_at'),
        Index('idx_access_status_date', 'status_code', 'created_at'),
        Index('idx_access_ip_date', 'ip_address', 'created_at'),
        {'comment': 'API access logs for monitoring and analytics'},
    )
    
    @hybrid_property
    def is_success(self):
        """Check if request was successful (2xx status code)"""
        return 200 <= self.status_code < 300
    
    @hybrid_property
    def is_error(self):
        """Check if request resulted in error (4xx or 5xx status code)"""
        return 400 <= self.status_code < 600
    
    def to_dict(self):
        """Convert access log to dictionary"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'method': self.method,
            'endpoint': self.endpoint,
            'status_code': self.status_code,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'duration': self.duration,
            'response_size': self.response_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_success': self.is_success,
            'is_error': self.is_error,
        }


# Export all models
__all__ = [
    'User',
    'SMSRecord',
    'TransactionCategory',
    'SMS_Category_Association',
    'SystemLog',
    'OTPRecord',
    'DashboardCache',
    'APIAccessLog',
    'TransactionType',
    'LogLevel',
]