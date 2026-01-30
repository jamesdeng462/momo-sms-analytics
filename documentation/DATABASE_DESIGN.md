# Database Design & Justification

## Design Rationale (288 words)

The MoMo SMS data processing system is characterized by a highly developed database, which has the capability to process the mobile money transaction records efficiently without compromising the data integrity, data scaling and the most efficient query operation. The key entities of this architecture are the following: Users, Transactions, Transaction Categories, Transaction Participants, and System Logs. 

Users table contains very important information of the senders and receivers with special restrictions on phone numbers to avoid duplications. The financial records are represented in transactions associated with both Users and Transaction_Categories that allow categorising the type of transaction and maintaining an appropriate level of referential integrity with the help of foreign keys. The junction table Transactions Parts will be used to maintain many-to-many relationships, so that it can record multiple participants of a specific transaction and their roles. 

Moreover, System_Logs will provide a powerful audit trail recording operations, and tracking of errors. Types and constraints are chosen with accuracy, using DECIMAL as the monetary value, ENUM as the status and DATETIME as the time. Primary and foreign keys are used to create indexes in order to improve performance of a query by a great margin and check constraints are present to ensure data are valid.

In the database design, the balance between normalization in order to ensure data consistency and practical denormalization to facilitate efficient reporting is reached. The architecture is designed with not only the requirement to serve the existing operational needs, but also to expand in the future, including the possibility of more types of transactions or integration via other payment platforms. Generally, it is in line with the best practices in the design of relational databases, especially financial applications that are reliable and robust in managing transactions.

# Database Design Document
## MoMo SMS Analytics System
### Team Eight: James Giir Deng & Byusa M Martin De Poles

## 1. Executive Summary

This document outlines the comprehensive database design for the MoMo SMS Analytics System. The system processes Mobile Money transaction data extracted from SMS backups, transforming unstructured text into structured, queryable information for analysis and reporting.

## 2. Design Philosophy

### 2.1 Principles
- **Normalization**: 3rd Normal Form (3NF) to eliminate redundancy
- **Performance**: Strategic indexing and partitioning
- **Security**: Row-level security and encryption
- **Scalability**: Horizontal and vertical scaling capabilities
- **Maintainability**: Clear naming conventions and documentation

### 2.2 Constraints
- **Referential Integrity**: All foreign keys enforced
- **Data Validation**: CHECK constraints for business rules
- **Consistency**: ACID compliance for transactions
- **Auditability**: Comprehensive logging and versioning

## 3. Entity Relationship Diagram

### 3.1 Overview
The ERD comprises 6 core entities with well-defined relationships:



┌─────────────────┐ ┌──────────────────┐ ┌─────────────────────┐
│ USERS       │◄────┤SMS_RECORDS ├─────► │TRANSACTION_CATEGORIES│
├─────────────────┤ ├──────────────────┤ ├─────────────────────┤
│ PK: id          │ │ PK: id           │ │ PK: id              │
│ phone_number    │ │ transaction_type │ │ name                │
│ full_name       │ │ amount           │ │ code                │
│ account_number  │ │ sender_id (FK)   │ │ description         │
│ is_active       │ │ receiver_id (FK) │ └─────────────────────┘
│ created_at      │ │ transaction_date │ │
│ updated_at      │ │ balance_after    │ │
└─────────────────┘ │ fee              │ │
                  │ │ transaction_id   │ │
                  │ │ is_parsed        │ │
▼                   └──────────────────┘ ▼
┌─────────────────┐ │                      ┌─────────────────────┐
│ OTP_RECORDS     │ │                      │  SMS_CATEGORY_ASSOC │
├─────────────────┤ │                      ├─────────────────────┤
│ PK: id          │ ▼                      │ PK: sms_id, cat_id  │
│ otp_code        │   ┌──────────────────┐ │ assigned_at         │
│ phone_number    │   │ SYSTEM_LOGS      │ └─────────────────────┘
│ is_used         │   ├──────────────────┤
│ expires_at      │   │ PK: id           │
│ created_at      │   │ level            │
└─────────────────┘   │ module           │
                      │ message          │
                      │ user_id (FK)     │
                      │ created_at       │
                      └──────────────────┘