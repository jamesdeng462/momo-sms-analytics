"""
Test Suite for MoMo SMS Analytics API
Team Eight: James Giir Deng & Byusa M Martin De Poles
"""
import pytest
import json
import base64
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from api.main import app
from api.database import Base, get_db
from api import models, crud

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Test client
client = TestClient(app)

# Authentication
AUTH_HEADER = {
    "Authorization": "Basic " + base64.b64encode(b"team5:ALU2025").decode("utf-8")
}

# Test data
TEST_USER = {
    "phone_number": "+250788888888",
    "full_name": "Test User",
    "account_number": "TEST001"
}

TEST_SMS = {
    "address": "M-Money",
    "body": "Test transaction message",
    "date": datetime.now().isoformat(),
    "readable_date": "27 Jan 2024 10:00:00 AM",
    "service_center": "+250788110381"
}

# Setup and teardown
@pytest.fixture(scope="function")
def test_db():
    """Create test database and yield session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

# Test classes
class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_root_endpoint_no_auth(self):
        """Test root endpoint without authentication"""
        response = client.get("/")
        assert response.status_code == 200
        assert "MoMo SMS Analytics API" in response.text
    
    def test_protected_endpoint_no_auth(self):
        """Test protected endpoint without authentication"""
        response = client.get("/api/transactions")
        assert response.status_code == 401
    
    def test_protected_endpoint_with_auth(self):
        """Test protected endpoint with authentication"""
        response = client.get("/api/transactions", headers=AUTH_HEADER)
        assert response.status_code == 200
    
    def test_invalid_credentials(self):
        """Test with invalid credentials"""
        invalid_auth = {
            "Authorization": "Basic " + base64.b64encode(b"wrong:wrong").decode("utf-8")
        }
        response = client.get("/api/transactions", headers=invalid_auth)
        assert response.status_code == 401

class TestTransactionEndpoints:
    """Test transaction CRUD endpoints"""
    
    def test_get_transactions(self, test_db):
        """Test getting all transactions"""
        response = client.get("/api/transactions", headers=AUTH_HEADER)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_transaction(self, test_db):
        """Test creating a transaction"""
        response = client.post(
            "/api/transactions",
            headers=AUTH_HEADER,
            json=TEST_SMS
        )
        assert response.status_code == 201
        data = response.json()
        assert data["address"] == TEST_SMS["address"]
        assert data["body"] == TEST_SMS["body"]
        assert "id" in data
    
    def test_get_single_transaction(self, test_db):
        """Test getting a single transaction"""
        # First create a transaction
        create_response = client.post(
            "/api/transactions",
            headers=AUTH_HEADER,
            json=TEST_SMS
        )
        transaction_id = create_response.json()["id"]
        
        # Then retrieve it
        response = client.get(
            f"/api/transactions/{transaction_id}",
            headers=AUTH_HEADER
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sms_record"]["id"] == transaction_id
    
    def test_update_transaction(self, test_db):
        """Test updating a transaction"""
        # Create transaction
        create_response = client.post(
            "/api/transactions",
            headers=AUTH_HEADER,
            json=TEST_SMS
        )
        transaction_id = create_response.json()["id"]
        
        # Update transaction
        update_data = {
            "transaction_type": "received",
            "amount": 5000.00,
            "is_parsed": True
        }
        
        response = client.put(
            f"/api/transactions/{transaction_id}",
            headers=AUTH_HEADER,
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_type"] == "received"
        assert float(data["amount"]) == 5000.00
        assert data["is_parsed"] == True
    
    def test_delete_transaction(self, test_db):
        """Test deleting a transaction"""
        # Create transaction
        create_response = client.post(
            "/api/transactions",
            headers=AUTH_HEADER,
            json=TEST_SMS
        )
        transaction_id = create_response.json()["id"]
        
        # Delete transaction
        response = client.delete(
            f"/api/transactions/{transaction_id}",
            headers=AUTH_HEADER
        )
        assert response.status_code == 200
        
        # Verify deletion
        get_response = client.get(
            f"/api/transactions/{transaction_id}",
            headers=AUTH_HEADER
        )
        assert get_response.status_code == 404
    
    def test_filter_transactions(self, test_db):
        """Test filtering transactions"""
        # Create multiple transactions with different types
        transactions = [
            {**TEST_SMS, "transaction_type": "received", "amount": 1000},
            {**TEST_SMS, "transaction_type": "sent", "amount": 500},
            {**TEST_SMS, "transaction_type": "deposit", "amount": 2000}
        ]
        
        for txn in transactions:
            client.post("/api/transactions", headers=AUTH_HEADER, json=txn)
        
        # Filter by type
        response = client.get(
            "/api/transactions?transaction_type=received",
            headers=AUTH_HEADER
        )
        assert response.status_code == 200
        data = response.json()
        assert all(txn["transaction_type"] == "received" for txn in data)
    
    def test_pagination(self, test_db):
        """Test transaction pagination"""
        # Create multiple transactions
        for i in range(15):
            txn = {**TEST_SMS, "body": f"Test transaction {i}"}
            client.post("/api/transactions", headers=AUTH_HEADER, json=txn)
        
        # Get first page
        response = client.get(
            "/api/transactions?skip=0&limit=10",
            headers=AUTH_HEADER
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10
        
        # Get second page
        response = client.get(
            "/api/transactions?skip=10&limit=10",
            headers=AUTH_HEADER
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5  # Only 5 remaining

class TestDashboardEndpoints:
    """Test dashboard analytics endpoints"""
    
    def test_dashboard_stats(self, test_db):
        """Test getting dashboard statistics"""
        response = client.get(
            "/api/dashboard/stats?days=7",
            headers=AUTH_HEADER
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "total_transactions" in data
        assert "total_amount" in data
        assert "average_transaction" in data
        assert "transaction_counts" in data
        assert "daily_volume" in data
        assert "top_senders" in data
        assert "top_receivers" in data
    
    def test_search_transactions(self, test_db):
        """Test searching transactions"""
        # Create a transaction with specific text
        txn = {
            **TEST_SMS,
            "body": "Payment to John Doe for services rendered",
            "sender_name": "John Doe",
            "receiver_name": "Jane Smith"
        }
        client.post("/api/transactions", headers=AUTH_HEADER, json=txn)
        
        # Search for it
        response = client.get(
            "/api/search?q=John",
            headers=AUTH_HEADER
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0
        assert "John" in json.dumps(data)

class TestSystemEndpoints:
    """Test system management endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/api/system/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
    
    def test_system_logs(self, test_db):
        """Test getting system logs"""
        response = client.get(
            "/api/system/logs",
            headers=AUTH_HEADER
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_export_transactions(self, test_db):
        """Test exporting transactions"""
        response = client.get(
            "/api/export/transactions?format=json",
            headers=AUTH_HEADER
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # Test CSV export
        response = client.get(
            "/api/export/transactions?format=csv",
            headers=AUTH_HEADER
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

class TestXMLParsing:
    """Test XML parsing functionality"""
    
    def test_xml_upload_invalid_file(self):
        """Test uploading invalid file"""
        files = {"file": ("test.txt", b"Not an XML file", "text/plain")}
        response = client.post(
            "/api/parse/xml",
            headers={"Authorization": AUTH_HEADER["Authorization"]},
            files=files
        )
        assert response.status_code == 400
    
    def test_xml_upload_no_file(self):
        """Test uploading without file"""
        response = client.post(
            "/api/parse/xml",
            headers={"Authorization": AUTH_HEADER["Authorization"]},
            data={}
        )
        assert response.status_code == 422  # Validation error

class TestErrorHandling:
    """Test error handling"""
    
    def test_nonexistent_endpoint(self):
        """Test accessing non-existent endpoint"""
        response = client.get("/api/nonexistent", headers=AUTH_HEADER)
        assert response.status_code == 404
    
    def test_invalid_transaction_id(self):
        """Test with invalid transaction ID"""
        response = client.get("/api/transactions/999999", headers=AUTH_HEADER)
        assert response.status_code == 404
    
    def test_invalid_json(self):
        """Test with invalid JSON"""
        response = client.post(
            "/api/transactions",
            headers={**AUTH_HEADER, "Content-Type": "application/json"},
            data="Invalid JSON"
        )
        assert response.status_code == 422
    
    def test_validation_errors(self):
        """Test validation errors"""
        invalid_sms = {
            "address": "",  # Empty address should fail
            "body": "Test",
            "date": "invalid-date"  # Invalid date format
        }
        response = client.post(
            "/api/transactions",
            headers=AUTH_HEADER,
            json=invalid_sms
        )
        assert response.status_code == 422

class TestPerformance:
    """Test performance of endpoints"""
    
    def test_response_time(self, test_db):
        """Test response time for dashboard endpoint"""
        import time
        
        start_time = time.time()
        response = client.get("/api/dashboard/stats", headers=AUTH_HEADER)
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # Response should be under 2 seconds
        assert response_time < 2.0, f"Response time too slow: {response_time}s"
    
    def test_concurrent_requests(self, test_db):
        """Test handling concurrent requests"""
        import threading
        
        results = []
        
        def make_request():
            response = client.get("/api/transactions", headers=AUTH_HEADER)
            results.append(response.status_code)
        
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert all(status == 200 for status in results)
        assert len(results) == 10

# Integration tests
class TestIntegration:
    """Integration tests"""
    
    def test_full_workflow(self, test_db):
        """Test complete workflow: create, update, delete"""
        # 1. Create transaction
        create_response = client.post(
            "/api/transactions",
            headers=AUTH_HEADER,
            json=TEST_SMS
        )
        assert create_response.status_code == 201
        transaction_id = create_response.json()["id"]
        
        # 2. Get transaction
        get_response = client.get(
            f"/api/transactions/{transaction_id}",
            headers=AUTH_HEADER
        )
        assert get_response.status_code == 200
        
        # 3. Update transaction
        update_response = client.put(
            f"/api/transactions/{transaction_id}",
            headers=AUTH_HEADER,
            json={"transaction_type": "received", "amount": 1000}
        )
        assert update_response.status_code == 200
        
        # 4. Get dashboard stats
        stats_response = client.get(
            "/api/dashboard/stats",
            headers=AUTH_HEADER
        )
        assert stats_response.status_code == 200
        
        # 5. Delete transaction
        delete_response = client.delete(
            f"/api/transactions/{transaction_id}",
            headers=AUTH_HEADER
        )
        assert delete_response.status_code == 200
        
        # 6. Verify deletion
        verify_response = client.get(
            f"/api/transactions/{transaction_id}",
            headers=AUTH_HEADER
        )
        assert verify_response.status_code == 404
    
    def test_data_consistency(self, test_db):
        """Test data consistency across operations"""
        # Create multiple transactions
        transactions = []
        for i in range(5):
            txn = {**TEST_SMS, "body": f"Transaction {i}", "amount": (i + 1) * 1000}
            response = client.post("/api/transactions", headers=AUTH_HEADER, json=txn)
            transactions.append(response.json())
        
        # Get all transactions
        response = client.get("/api/transactions", headers=AUTH_HEADER)
        all_transactions = response.json()
        
        # Verify count matches
        assert len(all_transactions) >= 5
        
        # Verify data integrity
        for created_txn in transactions:
            found = False
            for retrieved_txn in all_transactions:
                if retrieved_txn["id"] == created_txn["id"]:
                    assert retrieved_txn["body"] == created_txn["body"]
                    assert float(retrieved_txn.get("amount", 0)) == float(created_txn.get("amount", 0))
                    found = True
                    break
            assert found, f"Transaction {created_txn['id']} not found in retrieved data"

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])