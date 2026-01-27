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
