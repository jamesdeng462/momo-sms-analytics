import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal
import re
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from . import models, crud, schemas
from .database import SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse timestamp from various formats"""
    try:
        # Handle Unix timestamp in milliseconds
        if timestamp_str.isdigit() and len(timestamp_str) > 10:
            return datetime.fromtimestamp(int(timestamp_str) / 1000)
        
        # Handle date strings
        date_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%d %b %Y %I:%M:%S %p",
            "%Y%m%d%H%M%S"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        return datetime.now()
    except Exception as e:
        logger.error(f"Error parsing timestamp {timestamp_str}: {e}")
        return datetime.now()

def extract_amount(text: str) -> Optional[Decimal]:
    """Extract amount from SMS text"""
    amount_patterns = [
        r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*RWF',  # 1,600 RWF
        r'RWF\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',  # RWF 1,600
        r'(\d+(?:\.\d+)?)\s*RWF',  # 1600 RWF
        r'payment of (\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*RWF',  # payment of 1,600 RWF
        r'received (\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*RWF',  # received 25000 RWF
        r'deposit of (\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*RWF',  # deposit of 5000 RWF
        r'transferred (\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*RWF',  # transferred 700 RWF
    ]
    
    for pattern in amount_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                return Decimal(amount_str)
            except:
                continue
    
    return None

def extract_fee(text: str) -> Decimal:
    """Extract fee from SMS text"""
    fee_patterns = [
        r'Fee was:\s*(\d+(?:\.\d+)?)\s*RWF',
        r'Fee was (\d+(?:\.\d+)?)\s*RWF',
        r'Fee paid:\s*(\d+(?:\.\d+)?)\s*RWF',
    ]
    
    for pattern in fee_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return Decimal(match.group(1))
            except:
                continue
    
    return Decimal('0.0')

def extract_balance(text: str) -> Optional[Decimal]:
    """Extract balance from SMS text"""
    balance_patterns = [
        r'new balance:\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*RWF',
        r'NEW BALANCE\s*:\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*RWF',
        r'balance:\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*RWF',
        r'Your new balance\s*:\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*RWF',
    ]
    
    for pattern in balance_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            balance_str = match.group(1).replace(',', '')
            try:
                return Decimal(balance_str)
            except:
                continue
    
    return None

def extract_transaction_id(text: str) -> Optional[str]:
    """Extract transaction ID from SMS text"""
    patterns = [
        r'Transaction Id:\s*(\d+)',
        r'Financial Transaction Id:\s*(\d+)',
        r'TxId:\s*(\d+)',
        r'External Transaction Id:\s*(\d+)',
        r'Id:\s*(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    return None

def extract_names(text: str) -> Dict[str, Optional[str]]:
    """Extract sender and receiver names from SMS text"""
    result = {"sender": None, "receiver": None, "agent": None}
    
    # Sender patterns
    sender_patterns = [
        r'received.*?from\s+([A-Za-z\s]+?)\s+\(',  # received from Samuel Carter (
        r'by\s+([A-Za-z\s]+?)\s+on',  # by DIRECT PAYMENT LTD on
        r'from\s+([A-Za-z\s]+?)\s+\(',  # from Samuel Carter (
    ]
    
    # Receiver patterns
    receiver_patterns = [
        r'to\s+([A-Za-z\s]+?)\s+(\d+|\()',  # to Linda Green 14166 or to Jane Smith (250790777777)
        r'payment to\s+([A-Za-z\s]+?)\s+\d+',  # payment to Linda Green 14166
        r'transferred to\s+([A-Za-z\s]+?)\s+\d+',  # transferred to John Doe 12345    