CREATE TABLE sms_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    xml_id VARCHAR(100) UNIQUE,
    -- Original SMS data
    address VARCHAR(100) NOT NULL,
    body TEXT NOT NULL,
    date DATETIME NOT NULL,
    type INT DEFAULT 1,
    -- Parsed transaction data
    transaction_type ENUM(...),
    amount DECIMAL(12,2),
    fee DECIMAL(12,2) DEFAULT 0.00,
    balance_after DECIMAL(12,2),
    transaction_id VARCHAR(50) UNIQUE,
    -- Foreign keys
    sender_id INT,
    receiver_id INT,
    -- System metadata
    is_parsed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);