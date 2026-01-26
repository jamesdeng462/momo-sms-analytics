import base64
import json
import os

from http.server import HTTPServer, BaseHTTPRequestHandler

# Global lists to hold our data once the server starts
transactions = []        # We use this for Linear Search (slower, but keeps order)
transactions_dict = {}   # We use this for Dictionary Lookup (super fast O(1) speed)

def load_parsed_data():
    
    # Finds the JSON file in the ../dsa/ folder and loads it into memory.
  
    global transactions, transactions_dict
    
    # This path tells the script: "Go out of the api folder, look in dsa folder"
    json_path = os.path.join(os.path.dirname(__file__), '..', 'dsa', 'transactions.json')

    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            transactions = json.load(f)
            # We map the data to a dictionary right away so searching is instant later
            for txn in transactions:
                transactions_dict[txn['id']] = txn
        print(f" Success! Loaded {len(transactions)} records from {json_path}")
    else:
        print(f" Error:  couldn't find '{json_path}'. Did you run the parser first?")


class APIHandler(BaseHTTPRequestHandler):

    def check_login(self):
       # this code handles the security check
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
            print(f"Auth error: {e}")
            return False

    def do_GET(self):
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

def do_POST(self):
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

        self._send_json(new_data, 201)

    except Exception as e:
        self._send_json({"error": str(e)}, 400)















    def do_PUT(self):
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
                    transactions_dict[txn_id] = txn # Update the dictionary too
                    return self._send_json(txn)


            self._send_json({"error": "Not found"}, 404)

        except Exception:
            self._send_json({"error": "Update failed"}, 400)

def do_DELETE(self):

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

            self._send_json({"message": "Transaction deleted successfully"})
        else:
            self._send_json({"error": "ID not found"}, 404)

    except Exception:
        self._send_json({"error": "Delete failed"}, 400)

    def _send_json(self, data, status=200):
       
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        # We encode it to utf-8 so we don't get 'Parse Errors' in Postman
        json_output = json.dumps(data).encode('utf-8')
        self.send_header('Content-Length', str(len(json_output)))
        self.end_headers()
        self.wfile.write(json_output)

# Start the engine
if __name__ == '__main__':
    load_parsed_data()
    port = 8000
    server = HTTPServer(('localhost', port), APIHandler)
    print(f"--- MoMo API is live at http://localhost:{port} ---")
    print("Login: team5 | Password: ALU2025")
