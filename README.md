# momo-sms-analytics

# Team eight

# MoMo SMS Database Project

## Overview
This project implements a database system for processing Mobile Money (MoMo) SMS data.
It includes database design, ERD, SQL schema, and documentation aligned with academic requirements.

## Contents
- `docs/` – Documentation and ERD references
- `sql/` – Database schema and queries
- `data/` – Sample XML data
- `screenshots/` – CRUD operation evidence (to be added)

## ERD
ERD image is hosted externally:
https://drive.google.com/file/d/1h7vQbIIBTC_RX2CrcEjB_6oaFeiDz5Wz/view

Miro team structure:
https://miro.com/welcomeonboard/Qi83dFpSQWwvS2NWdXZjTDVQN3RxSjB6UmxMeFRTa2NaOTBXSjI2clN2OFIrY3Nva2haMmxRK1FMU2hzVzBUYkpPeUFINlFtT2JzVGNuMUdBMUw0T3lIbjRIeFlSOE5XcG92TjhiWXN0Ly9UNU9aMWdxYmU5dmhjcERsMWhZei9Bd044SHFHaVlWYWk0d3NxeHNmeG9BPT0hdjE=

## Security & Accuracy
- ENUM constraints
- CHECK constraints
- UNIQUE keys
- Foreign key enforcement


# Prokect resources
https://miro.com/app/board/uXjVGODnhYI=/

GitHub project tracker:  https://github.com/jamesdeng462/momo-sms-analytics/projects

 Tasksheet: https://docs.google.com/spreadsheets/d/1THFdLiZaV6xgZWTia84oIPlt42OrRqCsz-0TQMUID2U/edit?usp=sharing



# Repository Structure
The project follows a modular, enterprise-style architecture separating
ETL, data storage, API services, and frontend components.

## Team Eight Members
- **James Giir Deng** (Team Lead & Backend Developer)
- **Byusa M Martin De Poles** (Frontend Developer & Database Architect)

## Key Features
- **ETL Pipeline**: Parse raw XML SMS data into structured format
- **Database Management**: MySQL/SQLite with full ACID compliance
- **RESTful API**: FastAPI backend with authentication
- **Dashboard**: Interactive web dashboard for analytics
- **Security**: Role-based access control and data encryption
- **Scalability**: Modular design for enterprise deployment

## Technology Stack
- **Backend**: Python, FastAPI, SQLAlchemy
- **Database**: MySQL/SQLite
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js
- **DevOps**: Docker, GitHub Actions
- **Documentation**: Markdown, OpenAPI

## Repository Structure


momo-sms-analytics/
├── api/                          # FastAPI backend (updated from your existing)
│   ├── __init__.py
│   ├── main.py                   # FastAPI app with endpoints
│   ├── models.py                 # SQLAlchemy models
│   ├── database.py               # Database connection
│   ├── crud.py                   # CRUD operations
│   ├── schemas.py                # Pydantic schemas
│   ├── parse_xml.py              # XML parsing
│   ├── auth.py                   # Authentication
│   └── api_handler.py            # HTTP server (from your code)
├── data/                         # Data files
│   ├── sms_data.xml              # Full XML data
│   └── parsed_transactions.json  # Parsed JSON data
├── documentation/                # Documentation
│   ├── DATABASE_DESIGN.md
│   ├── API_DOCUMENTATION.md
│   └── SYSTEM_DESIGN.md
├── examples/                     # Examples
│   ├── json_schemas.json
│   └── sample_requests.py
├── images/                       # Images and diagrams
│   ├── erd.png
│   ├── miro_structure.png
│   └── api_screenshot.png
├── screenshots/                  # Operation screenshots
│   ├── crud_operations/
│   └── database_schema/
├── sql/                          # SQL files
│   ├── database_setup.sql
│   ├── sample_queries.sql
│   └── constraints.sql
├── dsa/                          # Data Structures folder
│   └── transactions.json         # For linear/dictionary search
├── frontend/                     # Frontend dashboard
│   ├── index.html
│   ├── styles.css
│   ├── script.js
│   └── dashboard.js
├── tests/                        # Test files
│   ├── test_api.py
│   ├── test_parsing.py
│   └── test_database.py
├── .env.example                  # Environment variables
├── requirements.txt              # Python dependencies
├── README.md                     # Main documentation
└── docker-compose.yml            # Docker setup



# Docker Deployment
bash
Copy
Download

# Build and run with Docker
docker-compose up -d

# View logs

docker-compose logs -f
API Documentation
Base URL: http://localhost:8000
Key Endpoints
Method	Endpoint	Description	Authentication
GET	/api/transactions	List all transactions	Basic Auth
GET	/api/transactions/{id}	Get specific transaction	Basic Auth
POST	/api/transactions	Create new transaction	Basic Auth
PUT	/api/transactions/{id}	Update transaction	Basic Auth
DELETE	/api/transactions/{id}	Delete transaction	Basic Auth
GET	/api/dashboard/stats	Dashboard statistics	Basic Auth
POST	/api/parse/xml	Parse XML file	Basic Auth

# Authentication
Username: team5
Password: ALU2025
Method: Basic Authentication

Usage Examples
Parse XML Data
python
Copy
Download

import requests
import base64

# Authentication
auth = base64.b64encode(b"team5:ALU2025").decode('utf-8')
headers = {"Authorization": f"Basic {auth}"}

# Parse XML
response = requests.post(
    "http://localhost:8000/api/parse/xml",
    headers=headers,
    files={"file": open("data/sms_data.xml", "rb")}
)
Query Transactions
bash
Copy
Download

# Using curl
curl -u "team5:ALU2025" http://localhost:8000/api/transactions

# Using Python
import requests
from requests.auth import HTTPBasicAuth

response = requests.get(
    "http://localhost:8000/api/transactions",
    auth=HTTPBasicAuth('team5', 'ALU2025')
)

# Dashboard Features
Transaction History: View all MoMo transactions
Analytics Charts: Visualize spending patterns
Category Breakdown: Analyze by transaction type
Search & Filter: Find specific transactions
Export Data: Download reports in JSON/CSV
Project Management

# Scrum Board
https://github.com/jamesdeng462/momo-sms-analytics/projects

# Task Sheet
https://docs.google.com/spreadsheets/d/1THFdLiZaV6xgZWTia84oIPlt42OrRqCsz-0TQMUID2U/

# Miro Board
https://miro.com/app/board/uXjVGODnhYI=/

# ERD Reference
https://drive.google.com/file/d/1h7vQbIIBTC_RX2CrcEjB_6oaFeiDz5Wz/view

# Development Guidelines

# Branch Strategy
main: Production-ready code
develop: Integration branch
feature: New features
bugfix: Bug fixes
hotfix: Critical fixes

# Commit Convention
feat: New feature
fix: Bug fix
docs: Documentation
style: Formatting
refactor: Code restructuring
test: Testing
chore: Maintenance

Testing
bash
Copy
Download

# Run all tests
python -m pytest tests/

# Run specific test module
python -m pytest tests/test_api.py

# Run with coverage
python -m pytest --cov=api tests/
Security Considerations
Data Encryption: Sensitive data encrypted at rest
Access Control: Role-based permissions
Input Validation: Sanitize all user inputs
SQL Injection: Parameterized queries only
Logging: Comprehensive audit trails
Error Handling: Graceful failure without data exposure

# Performance Optimization
Database Indexing: Strategic indexes on frequently queried columns
Query Optimization: Optimized JOIN operations
Caching: Redis cache for frequent queries
Pagination: Limit data transfer for large datasets
Compression: Gzip compression for API responses

# Contributing
Fork the repository
Create a feature branch (git checkout -b feature/AmazingFeature)
Commit changes (git commit -m 'Add AmazingFeature')
Push to branch (git push origin feature/AmazingFeature)
Open a Pull Request


# Acknowledgments
ALU: African Leadership University for academic guidance
MTN Rwanda: For sample MoMo SMS data patterns
Open Source Community: For invaluable tools and libraries

# Contact
James Giir Deng: james.deng@alustudent.com
Byusa M Martin De Poles: m.byusa@alustudent.com

