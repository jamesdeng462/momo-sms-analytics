CREATE TABLE system_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    level ENUM('INFO', 'WARNING', 'ERROR', 'DEBUG', 'CRITICAL'),
    module VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    details TEXT,
    user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);