from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from . import models, schemas

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# User CRUD Operations
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_phone(db: Session, phone_number: str):
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        phone_number=user.phone_number,
        full_name=user.full_name,
        account_number=user.account_number,
        is_active=user.is_active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True

# SMS Record CRUD Operations
def get_sms_record(db: Session, sms_id: int):
    return db.query(models.SMSRecord).filter(models.SMSRecord.id == sms_id).first()

def get_sms_by_transaction_id(db: Session, transaction_id: str):
    return db.query(models.SMSRecord).filter(
        models.SMSRecord.transaction_id == transaction_id
    ).first()

def get_sms_records(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    transaction_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None
):
    query = db.query(models.SMSRecord)
    
    if transaction_type:
        query = query.filter(models.SMSRecord.transaction_type == transaction_type)
    
    if start_date:
        query = query.filter(models.SMSRecord.transaction_date >= start_date)
    
    if end_date:
        query = query.filter(models.SMSRecord.transaction_date <= end_date)
    
    if min_amount:
        query = query.filter(models.SMSRecord.amount >= min_amount)
    
    if max_amount:
        query = query.filter(models.SMSRecord.amount <= max_amount)
    
    return query.order_by(desc(models.SMSRecord.date)).offset(skip).limit(limit).all()

def create_sms_record(db: Session, sms: schemas.SMSRecordCreate):
    db_sms = models.SMSRecord(
        address=sms.address,
        body=sms.body,
        date=sms.date,
        readable_date=sms.readable_date,
        service_center=sms.service_center,
        protocol=sms.protocol,
        type=sms.type,
        contact_name=sms.contact_name
    )
    db.add(db_sms)
    db.commit()
    db.refresh(db_sms)
    
    # Log the creation
    log_system_event(
        db,
        level="INFO",
        module="CRUD",
        message=f"Created SMS record {db_sms.id}",
        details=f"Address: {sms.address}, Date: {sms.date}"
    )
    
    return db_sms

def update_sms_record(db: Session, sms_id: int, sms_update: schemas.SMSRecordUpdate):
    db_sms = get_sms_record(db, sms_id)
    if not db_sms:
        return None
    
    update_data = sms_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_sms, field, value)
    
    db.commit()
    db.refresh(db_sms)
    return db_sms

def delete_sms_record(db: Session, sms_id: int):
    db_sms = get_sms_record(db, sms_id)
    if not db_sms:
        return False
    
    db.delete(db_sms)
    db.commit()
    
    log_system_event(
        db,
        level="WARNING",
        module="CRUD",
        message=f"Deleted SMS record {sms_id}",
        details=f"Transaction ID: {db_sms.transaction_id}"
    )
    
    return True

def search_sms_records(
    db: Session, 
    search_term: str,
    skip: int = 0,
    limit: int = 50
):
    """Search SMS records by various fields"""
    return db.query(models.SMSRecord).filter(
        or_(
            models.SMSRecord.body.ilike(f"%{search_term}%"),
            models.SMSRecord.sender_name.ilike(f"%{search_term}%"),
            models.SMSRecord.receiver_name.ilike(f"%{search_term}%"),
            models.SMSRecord.transaction_id.ilike(f"%{search_term}%")
        )
    ).offset(skip).limit(limit).all()

# Transaction Category Operations
def get_category(db: Session, category_id: int):
    return db.query(models.TransactionCategory).filter(
        models.TransactionCategory.id == category_id
    ).first()

def get_category_by_code(db: Session, code: str):
    return db.query(models.TransactionCategory).filter(
        models.TransactionCategory.code == code
    ).first()

def get_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.TransactionCategory).offset(skip).limit(limit).all()

def create_category(db: Session, category: schemas.TransactionCategoryCreate):
    db_category = models.TransactionCategory(
        name=category.name,
        description=category.description,
        code=category.code
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# System Log Operations
def log_system_event(
    db: Session,
    level: str,
    module: str,
    message: str,
    details: Optional[str] = None,
    user_id: Optional[int] = None
):
    db_log = models.SystemLog(
        level=level,
        module=module,
        message=message,
        details=details,
        user_id=user_id
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_system_logs(
    db: Session,
    level: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(models.SystemLog)
    
    if level:
        query = query.filter(models.SystemLog.level == level)
    
    if start_date:
        query = query.filter(models.SystemLog.created_at >= start_date)
    
    if end_date:
        query = query.filter(models.SystemLog.created_at <= end_date)
    
    return query.order_by(desc(models.SystemLog.created_at)).offset(skip).limit(limit).all()

# Analytics and Dashboard Functions
def get_dashboard_stats(db: Session, days: int = 30):
    """Get comprehensive dashboard statistics"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Total transactions
    total_txns = db.query(func.count(models.SMSRecord.id)).filter(
        models.SMSRecord.transaction_date.between(start_date, end_date)
    ).scalar() or 0
    
    # Total amount
    total_amount_result = db.query(func.sum(models.SMSRecord.amount)).filter(
        and_(
            models.SMSRecord.transaction_date.between(start_date, end_date),
            models.SMSRecord.amount.isnot(None)
        )
    ).scalar()
    total_amount = total_amount_result or Decimal('0.0')
    
    # Average transaction
    avg_txn = total_amount / total_txns if total_txns > 0 else Decimal('0.0')
    
    # Transaction counts by type
    type_counts = db.query(
        models.SMSRecord.transaction_type,
        func.count(models.SMSRecord.id).label('count')
    ).filter(
        models.SMSRecord.transaction_date.between(start_date, end_date)
    ).group_by(models.SMSRecord.transaction_type).all()
    
    transaction_counts = {str(t[0]): t[1] for t in type_counts if t[0]}
    
    # Daily volume
    daily_volume = db.query(
        func.date(models.SMSRecord.transaction_date).label('date'),
        func.count(models.SMSRecord.id).label('count'),
        func.sum(models.SMSRecord.amount).label('total')
    ).filter(
        models.SMSRecord.transaction_date.between(start_date, end_date)
    ).group_by(func.date(models.SMSRecord.transaction_date)).order_by('date').all()
    
    # Top senders
    top_senders = db.query(
        models.SMSRecord.sender_name,
        func.count(models.SMSRecord.id).label('txn_count'),
        func.sum(models.SMSRecord.amount).label('total_sent')
    ).filter(
        and_(
            models.SMSRecord.transaction_date.between(start_date, end_date),
            models.SMSRecord.sender_name.isnot(None)
        )
    ).group_by(models.SMSRecord.sender_name).order_by(desc('total_sent')).limit(10).all()
    
    # Top receivers
    top_receivers = db.query(
        models.SMSRecord.receiver_name,
        func.count(models.SMSRecord.id).label('txn_count'),
        func.sum(models.SMSRecord.amount).label('total_received')
    ).filter(
        and_(
            models.SMSRecord.transaction_date.between(start_date, end_date),
            models.SMSRecord.receiver_name.isnot(None)
        )
    ).group_by(models.SMSRecord.receiver_name).order_by(desc('total_received')).limit(10).all()
    
    return {
        "total_transactions": total_txns,
        "total_amount": total_amount,
        "average_transaction": avg_txn,
        "transaction_counts": transaction_counts,
        "daily_volume": [
            {
                "date": str(dv[0]),
                "count": dv[1],
                "total": dv[2] or Decimal('0.0')
            } for dv in daily_volume
        ],
        "top_senders": [
            {
                "name": ts[0],
                "transaction_count": ts[1],
                "total_sent": ts[2] or Decimal('0.0')
            } for ts in top_senders
        ],
        "top_receivers": [
            {
                "name": tr[0],
                "transaction_count": tr[1],
                "total_received": tr[2] or Decimal('0.0')
            } for tr in top_receivers
        ]
    }

def get_user_transaction_summary(db: Session, user_id: int):
    """Get transaction summary for a specific user"""
    user = get_user(db, user_id)
    if not user:
        return None
    
    # Sent transactions
    sent_stats = db.query(
        func.count(models.SMSRecord.id).label('count'),
        func.sum(models.SMSRecord.amount).label('total'),
        func.avg(models.SMSRecord.amount).label('average')
    ).filter(models.SMSRecord.sender_id == user_id).first()
    
    # Received transactions
    received_stats = db.query(
        func.count(models.SMSRecord.id).label('count'),
        func.sum(models.SMSRecord.amount).label('total'),
        func.avg(models.SMSRecord.amount).label('average')
    ).filter(models.SMSRecord.receiver_id == user_id).first()
    
    # Recent transactions
    recent_txns = db.query(models.SMSRecord).filter(
        or_(
            models.SMSRecord.sender_id == user_id,
            models.SMSRecord.receiver_id == user_id
        )
    ).order_by(desc(models.SMSRecord.date)).limit(10).all()
    
    return {
        "user": user,
        "sent": {
            "count": sent_stats[0] or 0,
            "total": sent_stats[1] or Decimal('0.0'),
            "average": sent_stats[2] or Decimal('0.0')
        },
        "received": {
            "count": received_stats[0] or 0,
            "total": received_stats[1] or Decimal('0.0'),
            "average": received_stats[2] or Decimal('0.0')
        },
        "recent_transactions": recent_txns
    }

# OTP Operations
def create_otp(db: Session, otp: schemas.OTPRecordCreate):
    db_otp = models.OTPRecord(
        otp_code=otp.otp_code,
        phone_number=otp.phone_number,
        purpose=otp.purpose,
        expires_at=otp.expires_at
    )
    db.add(db_otp)
    db.commit()
    db.refresh(db_otp)
    return db_otp

def validate_otp(db: Session, otp_code: str, phone_number: str):
    return db.query(models.OTPRecord).filter(
        and_(
            models.OTPRecord.otp_code == otp_code,
            models.OTPRecord.phone_number == phone_number,
            models.OTPRecord.is_used == False,
            models.OTPRecord.expires_at > datetime.now()
        )
    ).first()