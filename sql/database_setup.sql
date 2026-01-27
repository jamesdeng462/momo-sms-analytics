CREATE DATABASE momo_sms_db;
USE momo_sms_db;

-- USERS TABLE
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(100),
    user_type VARCHAR(20),
    account_balance DECIMAL(15,2) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    status VARCHAR(20)
);

-- TRANSACTION_CATEGORIES TABLE
CREATE TABLE transaction_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE,
    category_code VARCHAR(10) UNIQUE,
    description TEXT,
    transaction_fee_percentage DECIMAL(5,2),
    min_amount DECIMAL(15,2),
    max_amount DECIMAL(15,2),
    status VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- TRANSACTIONS TABLE
CREATE TABLE transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_ref VARCHAR(50) NOT NULL UNIQUE,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    category_id INT NOT NULL,
    amount DECIMAL(15,2) NOT NULL CHECK (amount > 0),
    fee DECIMAL(10,2) DEFAULT 0,
    total_amount DECIMAL(15,2) GENERATED ALWAYS AS (amount + fee) STORED,
    currency VARCHAR(3) DEFAULT 'RWF',
    transaction_date DATETIME NOT NULL,
    status VARCHAR(20),
    description TEXT,
    sms_content TEXT,
    source_system VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    FOREIGN KEY (sender_id) REFERENCES users(user_id),
    FOREIGN KEY (receiver_id) REFERENCES users(user_id),
    FOREIGN KEY (category_id) REFERENCES transaction_categories(category_id)
);

-- TRANSACTION_PARTICIPANTS TABLE (Junction)
CREATE TABLE transaction_participants (
    participant_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id INT NOT NULL,
    user_id INT NOT NULL,
    role VARCHAR(20),
    amount_impact DECIMAL(15,2),
    participated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- SYSTEM_LOGS TABLE
CREATE TABLE system_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id INT,
    user_id INT,
    log_level VARCHAR(20),
    log_type VARCHAR(50),
    log_message TEXT,
    error_details TEXT,
    processing_stage VARCHAR(50),
    logged_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    additional_metadata TEXT,
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);





USE momo_sms_db;

-- ======================
-- Sample USERS
-- ======================
INSERT INTO users (phone_number, full_name, user_type, account_balance, status)
VALUES 
('250790777777', 'Jane Smith', 'customer', 46449, 'active'),
('250789888888', 'Alex Doe', 'customer', 107487, 'active'),
('250790777777', 'Linda Deslem', 'customer', 111487, 'active'),
('250788999999', 'Samuel Carter', 'customer', 67993, 'active'),
('250789888888', 'Robert Brown', 'customer', 123087, 'active');

-- ======================
-- Sample TRANSACTION CATEGORIES
-- ======================
INSERT INTO transaction_categories (category_name, category_code, description, transaction_fee_percentage, min_amount, max_amount, status)
VALUES
('Deposit', 'DEP', 'Cash deposits to account', 0, 100, 1000000, 'active'),
('Transfer', 'TRF', 'Money transferred to another user', 2, 100, 500000, 'active'),
('Payment', 'PAY', 'Payments for services or goods', 1, 100, 100000, 'active');

-- ======================
-- Sample TRANSACTIONS
-- ======================
INSERT INTO transactions (transaction_ref, sender_id, receiver_id, category_id, amount, fee, transaction_date, status, description, sms_content, source_system)
VALUES
('TX20250102A', 1, 0, 1, 3600, 100, '2025-01-02 23:15:06', 'completed', 'Transfer to Jane Smith', '*165*S*3600 RWF transferred to Jane Smith ...', 'M-Money'),
('TX20250103A', 2, 0, 2, 15500, 250, '2025-01-03 20:40:38', 'completed', 'Transfer to Jane Smith', '*165*S*15500 RWF transferred to Jane Smith ...', 'M-Money'),
('TX20250103B', 3, 0, 3, 5400, 0, '2025-01-03 22:04:05', 'completed', 'Payment to Linda Deslem', 'TxId: 47955567230. Your payment of 5,400 RWF to Linda Deslem ...', 'M-Money'),
('TX20250104A', 4, 0, 2, 1000, 20, '2025-01-04 21:31:50', 'completed', 'Transfer to Alex Doe', '*165*S*1000 RWF transferred to Alex Doe ...', 'M-Money'),
('TX20250105A', 5, 0, 2, 40000, 250, '2025-01-06 21:20:35', 'completed', 'Transfer to Robert Brown', '*165*S*40000 RWF transferred to Robert Brown ...', 'M-Money');

-- ======================
-- Sample TRANSACTION PARTICIPANTS
-- ======================
INSERT INTO transaction_participants (transaction_id, user_id, role, amount_impact)
VALUES
(1, 1, 'sender', -3600),
(1, 2, 'receiver', 3600),
(2, 1, 'sender', -15500),
(2, 2, 'receiver', 15500),
(3, 3, 'sender', -5400),
(3, 4, 'receiver', 5400),
(4, 4, 'sender', -1000),
(4, 3, 'receiver', 1000),
(5, 5, 'sender', -40000),
(5, 5, 'receiver', 40000); -- Example if self-transfer

-- ======================
-- Sample SYSTEM LOGS
-- ======================
INSERT INTO system_logs (transaction_id, user_id, log_level, log_type, log_message, processing_stage, ip_address)
VALUES
(1, 1, 'INFO', 'TransactionCreated', 'Transaction created successfully', 'validation', '192.168.0.1'),
(2, 1, 'INFO', 'TransactionProcessed', 'Transaction processed successfully', 'completed', '192.168.0.1'),
(3, 3, 'INFO', 'TransactionProcessed', 'Transaction processed successfully', 'completed', '192.168.0.2'),
(4, 4, 'INFO', 'TransactionProcessed', 'Transaction processed successfully', 'completed', '192.168.0.3'),
(5, 5, 'INFO', 'TransactionProcessed', 'Transaction processed successfully', 'completed', '192.168.0.4');
