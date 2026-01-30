import base64
import json
import os
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
DB_PATH = Path("data/momo_transactions.db")

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT UNIQUE,
        amount REAL,
        currency TEXT DEFAULT 'RWF',
        transaction_type TEXT,
        sender_name TEXT,
        receiver_name TEXT,
        sender_phone TEXT,
        receiver_phone TEXT,
        date DATETIME,
        balance_after REAL,
        fee REAL DEFAULT 0,
        status TEXT DEFAULT 'completed',
        parsed_from TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_number TEXT UNIQUE,
        full_name TEXT,
        account_number TEXT UNIQUE,
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

# Global lists to hold our data once the server starts
transactions = []        # We use this for Linear Search (slower, but keeps order)
transactions_dict = {}   # We use this for Dictionary Lookup (super fast O(1) speed)

def load_parsed_data():
    """Load parsed data from JSON file and database"""
    global transactions, transactions_dict
    
    # Initialize database
    init_database()
    
    # Load from JSON file (DSA implementation)
    json_path = Path("dsa/transactions.json")
    if json_path.exists():
        with open(json_path, 'r') as f:
            transactions = json.load(f)
            # We map the data to a dictionary right away so searching is instant later
            for txn in transactions:
                transactions_dict[txn['id']] = txn
        logger.info(f"Success! Loaded {len(transactions)} records from {json_path}")
    else:
        logger.warning(f"Warning: Couldn't find '{json_path}'. Did you run the parser first?")
    
    # Load from database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM transactions')
    db_transactions = cursor.fetchall()
    
    for txn in db_transactions:
        txn_dict = {
            'id': txn[0],
            'transaction_id': txn[1],
            'amount': txn[2],
            'currency': txn[3],
            'transaction_type': txn[4],
            'sender_name': txn[5],
            'receiver_name': txn[6],
            'sender_phone': txn[7],
            'receiver_phone': txn[8],
            'date': txn[9],
            'balance_after': txn[10],
            'fee': txn[11],
            'status': txn[12],
            'parsed_from': txn[13],
            'created_at': txn[14]
        }
        
        # Add to both data structures
        transactions.append(txn_dict)
        transactions_dict[txn[0]] = txn_dict
    
    conn.close()
    logger.info(f"Loaded {len(db_transactions)} records from database")

class APIHandler(BaseHTTPRequestHandler):
    def check_login(self):
        """Handle authentication"""
        auth_header = self.headers.get('Authorization')
        if not auth_header:
            return False

        try:
            # The header looks like 'Basic [Base64String]', so we split it
            auth_type, encoded_creds = auth_header.split(' ', 1)
            if auth_type != 'Basic':
                return False

            # Decrypt the string to check the username/password
            decoded = base64.b64decode(encoded_creds).decode('utf-8')
            return decoded == "team5:ALU2025"
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return False

    def do_GET(self):
        """Handle GET requests"""
        # First, check if the user is allowed in
        if not self.check_login():
            self.send_response(401)
            # This header is what triggers the popup box in your browser!
            self.send_header('WWW-Authenticate', 'Basic realm="MoMo API"')
            self.end_headers()
            self.wfile.write(b'{"error": "Unauthorized. Please login."}')
            return

        # Path 1: Get all transactions
        if self.path == '/transactions':
            self._send_json(transactions)
        
        # Path 2: Get one specific transaction by ID
        elif self.path.startswith('/transactions/'):
            try:
                # Grab the ID from the end of the URL
                txn_id = int(self.path.split('/')[-1])

                # DSA Efficiency: We use the Dictionary here for O(1) lookup
                txn = transactions_dict.get(txn_id)

                if txn:
                    self._send_json(txn)
                else:
                    self._send_json({"error": "Transaction not found"}, 404)

            except ValueError:
                self._send_json({"error": "Invalid ID format"}, 400)
        
        # Path 3: Health check
        elif self.path == '/health':
            self._send_json({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "transaction_count": len(transactions)
            })
        
        # Path 4: Statistics
        elif self.path == '/stats':
            stats = self._calculate_statistics()
            self._send_json(stats)
        
        else:
            self._send_json({"error": "Endpoint not found"}, 404)

    def do_POST(self):
        """Handle POST requests"""
        if not self.check_login():
            self.send_response(401)
            self.end_headers()
            return

        try:
            # Figure out how much data the user is sending
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            new_data = json.loads(body)

            # Assign a new ID (just the next number in line)
            new_id = len(transactions) + 1
            new_data['id'] = new_id

            # Save it to both our memory structures
            transactions.append(new_data)
            transactions_dict[new_id] = new_data
            
            # Also save to database
            self._save_to_database(new_data)

            self._send_json(new_data, 201)

        except Exception as e:
            logger.error(f"POST error: {e}")
            self._send_json({"error": str(e)}, 400)

    def do_PUT(self):
        """Handle PUT requests"""
        if not self.check_login():
            self.send_response(401)
            self.end_headers()
            return

        try:
            txn_id = int(self.path.split('/')[-1])
            length = int(self.headers.get('Content-Length', 0))
            updated_fields = json.loads(self.rfile.read(length))

            # DSA Comparison: Using Linear Search (O(n)) to find the item in the list
            for txn in transactions:
                if txn['id'] == txn_id:
                    txn.update(updated_fields)
                    transactions_dict[txn_id] = txn  # Update the dictionary too
                    
                    # Update database
                    self._update_in_database(txn_id, updated_fields)
                    
                    return self._send_json(txn)

            self._send_json({"error": "Not found"}, 404)

        except Exception as e:
            logger.error(f"PUT error: {e}")
            self._send_json({"error": "Update failed"}, 400)

    def do_DELETE(self):
        """Handle DELETE requests"""
        if not self.check_login():
            self.send_response(401)
            self.end_headers()
            return

        try:
            txn_id = int(self.path.split('/')[-1])
            if txn_id in transactions_dict:
                # Remove it from the dictionary (Fast)
                del transactions_dict[txn_id]
                # Re-build the list without that ID (Slower)
                global transactions
                transactions = [t for t in transactions if t['id'] != txn_id]
                
                # Delete from database
                self._delete_from_database(txn_id)

                self._send_json({"message": "Transaction deleted successfully"})
            else:
                self._send_json({"error": "ID not found"}, 404)

        except Exception as e:
            logger.error(f"DELETE error: {e}")
            self._send_json({"error": "Delete failed"}, 400)

    def _send_json(self, data, status=200):
        """Helper method to send JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        # We encode it to utf-8 so we don't get 'Parse Errors' in Postman
        json_output = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_header('Content-Length', str(len(json_output)))
        self.end_headers()
        self.wfile.write(json_output)

    def _calculate_statistics(self):
        """Calculate transaction statistics"""
        if not transactions:
            return {"total": 0, "average": 0, "types": {}}
        
        total_amount = 0
        type_counts = {}
        
        for txn in transactions:
            if 'amount' in txn and txn['amount']:
                total_amount += float(txn['amount'])
            
            txn_type = txn.get('transaction_type', 'unknown')
            type_counts[txn_type] = type_counts.get(txn_type, 0) + 1
        
        return {
            "total_transactions": len(transactions),
            "total_amount": total_amount,
            "average_amount": total_amount / len(transactions) if transactions else 0,
            "transaction_types": type_counts,
            "timestamp": datetime.now().isoformat()
        }

    def _save_to_database(self, data):
        """Save transaction to SQLite database"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT OR REPLACE INTO transactions 
            (transaction_id, amount, currency, transaction_type, sender_name, 
             receiver_name, sender_phone, receiver_phone, date, balance_after, 
             fee, status, parsed_from)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('transaction_id'),
                data.get('amount'),
                data.get('currency', 'RWF'),
                data.get('transaction_type'),
                data.get('sender_name'),
                data.get('receiver_name'),
                data.get('sender_phone'),
                data.get('receiver_phone'),
                data.get('date'),
                data.get('balance_after'),
                data.get('fee', 0),
                data.get('status', 'completed'),
                data.get('parsed_from', 'api')
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Saved transaction {data.get('id')} to database")
        except Exception as e:
            logger.error(f"Error saving to database: {e}")

    def _update_in_database(self, txn_id, updates):
        """Update transaction in database"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Build update query
            set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values())
            values.append(txn_id)
            
            cursor.execute(f'''
            UPDATE transactions SET {set_clause} WHERE id = ?
            ''', values)
            
            conn.commit()
            conn.close()
            logger.info(f"Updated transaction {txn_id} in database")
        except Exception as e:
            logger.error(f"Error updating database: {e}")

    def _delete_from_database(self, txn_id):
        """Delete transaction from database"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM transactions WHERE id = ?', (txn_id,))
            
            conn.commit()
            conn.close()
            logger.info(f"Deleted transaction {txn_id} from database")
        except Exception as e:
            logger.error(f"Error deleting from database: {e}")

    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(format % args)

# Start the server
if __name__ == '__main__':
    load_parsed_data()
    port = 8080  # Different port from FastAPI
    server = HTTPServer(('localhost', port), APIHandler)
    logger.info(f"--- Legacy MoMo API is live at http://localhost:{port} ---")
    logger.info("Login: team5 | Password: ALU2025")
    logger.info("Use this for DSA testing and legacy support")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")