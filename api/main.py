"""
Main FastAPI Application for MoMo SMS Analytics System
Team Eight: James Giir Deng & Byusa M Martin De Poles
"""
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, BackgroundTasks
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import base64
import logging
from pathlib import Path

from sqlalchemy.orm import Session
from . import crud, schemas, models, parse_xml, auth
from .database import engine, SessionLocal, init_db
from .api_handler import load_parsed_data  # Import your existing HTTP handler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MoMo SMS Analytics API",
    description="API for processing and analyzing Mobile Money SMS data",
    version="1.0.0",
    contact={
        "name": "Team Eight",
        "email": "team8@alustudent.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBasic()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()
    load_parsed_data()  # Load data from your existing handler
    logger.info("Application started successfully")

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API documentation"""
    return """
    <html>
        <head>
            <title>MoMo SMS Analytics API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
                .endpoint { background: #f4f4f4; padding: 10px; margin: 10px 0; }
                code { background: #eee; padding: 2px 4px; }
            </style>
        </head>
        <body>
            <h1>MoMo SMS Analytics API</h1>
            <p>Welcome to the Mobile Money SMS Analytics System API</p>
            
            <h2>Available Endpoints:</h2>
            
            <div class="endpoint">
                <strong>GET /api/transactions</strong>
                <p>Get all transactions (requires authentication)</p>
                <code>curl -u team5:ALU2025 http://localhost:8000/api/transactions</code>
            </div>
            
            <div class="endpoint">
                <strong>GET /api/transactions/{id}</strong>
                <p>Get specific transaction by ID</p>
            </div>
            
            <div class="endpoint">
                <strong>POST /api/parse/xml</strong>
                <p>Upload and parse XML SMS data</p>
            </div>
            
            <div class="endpoint">
                <strong>GET /api/dashboard/stats</strong>
                <p>Get dashboard statistics</p>
            </div>
            
            <div class="endpoint">
                <strong>GET /docs</strong>
                <p>Interactive API documentation (Swagger UI)</p>
            </div>
            
            <div class="endpoint">
                <strong>GET /redoc</strong>
                <p>Alternative API documentation (ReDoc)</p>
            </div>
            
            <h2>Authentication</h2>
            <p>Username: <code>team5</code></p>
            <p>Password: <code>ALU2025</code></p>
            <p>Use Basic Authentication for all protected endpoints.</p>
            
            <h2>Team Members</h2>
            <ul>
                <li>James Giir Deng (Team Lead)</li>
                <li>Byusa M Martin De Poles</li>
            </ul>
            
            <footer>
                <p>© 2024 Team Eight - ALU Data Systems Assignment</p>
            </footer>
        </body>
    </html>
    """

# Authentication function
async def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify Basic Authentication credentials"""
    correct_username = "team5"
    correct_password = "ALU2025"
    
    if not (credentials.username == correct_username and credentials.password == correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Transaction endpoints
@app.get("/api/transactions", response_model=List[schemas.SMSRecord])
async def get_transactions(
    skip: int = 0,
    limit: int = 100,
    transaction_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    username: str = Depends(verify_credentials)
):
    """Get all transactions with optional filtering"""
    transactions = crud.get_sms_records(
        db, skip=skip, limit=limit,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date
    )
    return transactions

@app.get("/api/transactions/{transaction_id}", response_model=schemas.CompleteTransaction)
async def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    username: str = Depends(verify_credentials)
):
    """Get a specific transaction by ID"""
    transaction = crud.get_sms_record(db, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get related data
    sender = crud.get_user(db, transaction.sender_id) if transaction.sender_id else None
    receiver = crud.get_user(db, transaction.receiver_id) if transaction.receiver_id else None
    
    return {
        "sms_record": transaction,
        "sender": sender,
        "receiver": receiver,
        "categories": transaction.categories,
        "logs": []
    }

@app.post("/api/transactions", response_model=schemas.SMSRecord, status_code=201)
async def create_transaction(
    transaction: schemas.SMSRecordCreate,
    db: Session = Depends(get_db),
    username: str = Depends(verify_credentials)
):
    """Create a new transaction record"""
    return crud.create_sms_record(db, transaction)

@app.put("/api/transactions/{transaction_id}", response_model=schemas.SMSRecord)
async def update_transaction(
    transaction_id: int,
    transaction_update: schemas.SMSRecordUpdate,
    db: Session = Depends(get_db),
    username: str = Depends(verify_credentials)
):
    """Update an existing transaction"""
    transaction = crud.update_sms_record(db, transaction_id, transaction_update)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@app.delete("/api/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    username: str = Depends(verify_credentials)
):
    """Delete a transaction"""
    success = crud.delete_sms_record(db, transaction_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted successfully"}

# XML Parsing endpoint
@app.post("/api/parse/xml")
async def parse_xml_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    username: str = Depends(verify_credentials)
):
    """Parse XML SMS file and store in database"""
    if not file.filename.endswith('.xml'):
        raise HTTPException(status_code=400, detail="File must be XML")
    
    try:
        # Read file content
        content = await file.read()
        
        # Save to temporary file
        temp_path = Path(f"data/temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml")
        temp_path.parent.mkdir(exist_ok=True)
        temp_path.write_bytes(content)
        
        # Parse in background
        background_tasks.add_task(parse_xml.process_xml_file, str(temp_path), db)
        
        return {
            "message": "XML file uploaded successfully. Processing in background.",
            "filename": file.filename,
            "size": len(content)
        }
    except Exception as e:
        logger.error(f"Error processing XML file: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# Dashboard endpoints
@app.get("/api/dashboard/stats", response_model=schemas.DashboardStats)
async def get_dashboard_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    username: str = Depends(verify_credentials)
):
    """Get dashboard statistics"""
    stats = crud.get_dashboard_stats(db, days=days)
    return stats

@app.get("/api/dashboard/user/{user_id}")
async def get_user_dashboard(
    user_id: int,
    db: Session = Depends(get_db),
    username: str = Depends(verify_credentials)
):
    """Get dashboard data for specific user"""
    summary = crud.get_user_transaction_summary(db, user_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="User not found")
    return summary

# Search endpoint
@app.get("/api/search")
async def search_transactions(
    q: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    username: str = Depends(verify_credentials)
):
    """Search transactions by text"""
    results = crud.search_sms_records(db, search_term=q, skip=skip, limit=limit)
    return {
        "query": q,
        "results": results,
        "count": len(results)
    }

# System endpoints
@app.get("/api/system/logs")
async def get_system_logs(
    level: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    username: str = Depends(verify_credentials)
):
    """Get system logs"""
    logs = crud.get_system_logs(
        db, level=level, start_date=start_date,
        end_date=end_date, skip=skip, limit=limit
    )
    return logs

@app.get("/api/system/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database connection
        db.execute("SELECT 1")
        
        # Get some statistics
        total_transactions = db.query(models.SMSRecord).count()
        total_users = db.query(models.User).count()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "statistics": {
                "total_transactions": total_transactions,
                "total_users": total_users
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Export endpoints
@app.get("/api/export/transactions")
async def export_transactions(
    format: str = "json",
    db: Session = Depends(get_db),
    username: str = Depends(verify_credentials)
):
    """Export transactions in specified format"""
    transactions = crud.get_sms_records(db, skip=0, limit=1000)
    
    if format == "json":
        return JSONResponse(
            content=[schemas.SMSRecord.from_orm(t).dict() for t in transactions],
            media_type="application/json"
        )
    elif format == "csv":
        # Convert to CSV
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["ID", "Date", "Type", "Amount", "Sender", "Receiver", "Balance"])
        
        # Write data
        for t in transactions:
            writer.writerow([
                t.id,
                t.transaction_date.isoformat() if t.transaction_date else "",
                t.transaction_type.value if t.transaction_type else "",
                str(t.amount) if t.amount else "",
                t.sender_name or "",
                t.receiver_name or "",
                str(t.balance_after) if t.balance_after else ""
            ])
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=transactions.csv"}
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'json' or 'csv'.")

# Legacy API endpoints (from your existing code)
@app.get("/transactions", include_in_schema=False)
async def legacy_get_transactions():
    """Legacy endpoint - redirects to new API"""
    return {"message": "This endpoint is deprecated. Use /api/transactions instead."}

# Serve frontend files
frontend_path = Path("frontend")
if frontend_path.exists():
    app.mount("/dashboard", StaticFiles(directory="frontend", html=True), name="frontend")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)