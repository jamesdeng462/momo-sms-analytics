"""
Database configuration and connection management
Team Eight: James Giir Deng & Byusa M Martin De Poles
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.event import listens_for
from sqlalchemy.engine import Engine
from contextlib import contextmanager
import logging
from typing import Generator
import time

logger = logging.getLogger(__name__)

# Get database URL from environment or use default
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./momo_sms.db"
)

# Configure engine with connection pooling
engine_kwargs = {
    "poolclass": QueuePool,
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
}

# SQLite specific configuration
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    engine_kwargs["poolclass"] = None  # SQLite doesn't need connection pooling
# MySQL specific configuration
elif "mysql" in DATABASE_URL:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 299
# PostgreSQL specific configuration
elif "postgresql" in DATABASE_URL:
    engine_kwargs["pool_size"] = 20
    engine_kwargs["max_overflow"] = 40

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, **engine_kwargs)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

Base = declarative_base()

# Add query logging for debugging
@listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())
    logger.debug(f"Starting query: {statement}")

@listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 0.5:  # Log slow queries (more than 500ms)
        logger.warning(f"Slow query ({total:.3f}s): {statement}")

def get_db() -> Generator:
    """
    Dependency to get database session.
    Use in FastAPI dependencies.
    
    Usage:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            return crud.get_items(db)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()

@contextmanager
def db_session():
    """
    Context manager for database sessions.
    Use for non-FastAPI contexts.
    
    Usage:
        with db_session() as session:
            session.add(item)
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

def init_db():
    """
    Initialize database by creating all tables.
    
    This should be called on application startup.
    """
    try:
        # Import all models here to ensure they are registered
        from . import models
        Base.metadata.create_all(bind=engine)
        
        # Create default transaction categories
        with db_session() as db:
            # Check if categories already exist
            from .crud import get_category_by_code
            from .models import TransactionCategory
            
            default_categories = [
                {"name": "Money Transfer", "code": "TRANSFER", "description": "Transfer of funds to another user"},
                {"name": "Bank Deposit", "code": "DEPOSIT", "description": "Deposit from bank to mobile money"},
                {"name": "Withdrawal", "code": "WITHDRAW", "description": "Cash withdrawal from agent"},
                {"name": "Payment", "code": "PAYMENT", "description": "Payment for goods/services"},
                {"name": "Airtime Purchase", "code": "AIRTIME", "description": "Purchase of mobile airtime"},
                {"name": "Bill Payment", "code": "BILL", "description": "Payment of utility bills"},
                {"name": "Cash Power", "code": "POWER", "description": "Electricity token purchase"},
                {"name": "Salary", "code": "SALARY", "description": "Salary or payment received"},
                {"name": "Refund", "code": "REFUND", "description": "Refund of previous transaction"},
                {"name": "Commission", "code": "COMM", "description": "Agent commission"},
            ]
            
            for cat_data in default_categories:
                existing = get_category_by_code(db, cat_data["code"])
                if not existing:
                    category = TransactionCategory(**cat_data)
                    db.add(category)
            
            db.commit()
        
        logger.info("✅ Database initialized successfully!")
        
        # Log system event
        with db_session() as db:
            from .models import SystemLog
            log = SystemLog(
                level="INFO",
                module="Database",
                message="Database initialized successfully",
                details=f"Database URL: {DATABASE_URL}"
            )
            db.add(log)
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

def check_database_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def get_database_stats() -> dict:
    """
    Get database statistics.
    
    Returns:
        dict: Database statistics including table counts
    """
    stats = {}
    try:
        with db_session() as db:
            from . import models
            
            # Get count for each table
            tables = [
                ("users", models.User),
                ("sms_records", models.SMSRecord),
                ("transaction_categories", models.TransactionCategory),
                ("system_logs", models.SystemLog),
                ("otp_records", models.OTPRecord),
            ]
            
            for table_name, model in tables:
                count = db.query(model).count()
                stats[table_name] = count
            
            # Get database size (for supported databases)
            if "sqlite" in DATABASE_URL:
                result = db.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()").fetchone()
                if result:
                    stats["database_size_bytes"] = result[0]
            
            stats["connection_status"] = "connected"
            stats["database_url"] = DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL
            
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        stats["connection_status"] = "error"
        stats["error"] = str(e)
    
    return stats

# Create database connection pool metrics
class DatabaseMetrics:
    """Track database connection metrics"""
    
    def __init__(self):
        self.connections_checked_out = 0
        self.connections_returned = 0
        self.connection_errors = 0
    
    def increment_checked_out(self):
        self.connections_checked_out += 1
    
    def increment_returned(self):
        self.connections_returned += 1
    
    def increment_errors(self):
        self.connection_errors += 1
    
    def get_metrics(self) -> dict:
        return {
            "connections_checked_out": self.connections_checked_out,
            "connections_returned": self.connections_returned,
            "connection_errors": self.connection_errors,
            "active_connections": self.connections_checked_out - self.connections_returned,
        }

# Global metrics instance
db_metrics = DatabaseMetrics()

# Listen for connection events
@listens_for(engine, "checkout")
def checkout_listener(dbapi_con, con_record, con_proxy):
    db_metrics.increment_checked_out()
    logger.debug("Database connection checked out")

@listens_for(engine, "checkin")
def checkin_listener(dbapi_con, con_record):
    db_metrics.increment_returned()
    logger.debug("Database connection checked in")