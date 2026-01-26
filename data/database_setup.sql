 INDEX idx_timestamp     (timestamp),
  INDEX idx_sender        (sender_id),
  INDEX idx_receiver      (receiver_id),
  INDEX idx_tx_ref        (tx_ref),
  INDEX idx_category_time (category_id, timestamp)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
  COMMENT 'Mobile money transactions from SMS parsing';

-- Labels/tags for transactions
CREATE TABLE labels (
  label_id    INT AUTO_INCREMENT PRIMARY KEY,
  label_name  VARCHAR(75) NOT NULL UNIQUE COMMENT 'Tag name (Normal, Fraud Risk, etc.)',
  created_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
  COMMENT 'Classification tags for transactions';

-- Link transactions to multiple labels
CREATE TABLE transaction_labels (
  transaction_id INT      NOT NULL,
  label_id       INT      NOT NULL,
  assigned_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  PRIMARY KEY (transaction_id, label_id),

  CONSTRAINT fk_txl_tx     FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_txl_label  FOREIGN KEY (label_id)      REFERENCES labels(label_id)      ON DELETE CASCADE ON UPDATE CASCADE,

  INDEX idx_label (label_id)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
  COMMENT 'Assigns labels to transactions';

-- Audit log for system operations
CREATE TABLE system_logs (
  log_id         INT AUTO_INCREMENT PRIMARY KEY,
  tx_ref         VARCHAR(64) NULL COMMENT 'Transaction reference (null if parse failed)',
  transaction_id INT      NULL COMMENT 'Link to transaction if successfully parsed',
  log_level      ENUM('INFO', 'WARNING', 'ERROR', 'DEBUG') NOT NULL DEFAULT 'INFO',
  message        TEXT     NOT NULL COMMENT 'Log message',
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_log_tx FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE SET NULL ON UPDATE CASCADE,

  INDEX idx_log_tx_ref    (tx_ref),
  INDEX idx_log_created   (created_at),
  INDEX idx_log_level     (log_level)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
  COMMENT 'System logs for SMS parsing and processing';

-- Sample users
INSERT INTO users (phone_number, full_name) VALUES
(254759400001, 'Sadio Mane'),
(254784060258, 'Hassan Joho'),
(254795354678, 'Lionel Messi'),
(254748084162, 'Methode Duhujubumwe'),
(254790938315, 'Martin de Poles'),
(254740184611, 'Lul Deng'),
(254748084169, 'James Deng');

-- Transaction types
INSERT INTO categories (name) VALUES
('Airtime Purchase'),
('P2P Transfer'),
('Utility Bill Payment'),
('Merchant POS Payment'),
('International Remittance'),
('Cash Out / Withdrawal');

-- Transaction tags
INSERT INTO labels (label_name) VALUES
('Normal'),
('High Value'),
('Potential Fraud'),
('Promo Transaction'),
('Reversal Requested'),
('Family Support');

-- Sample transactions
INSERT INTO transactions (tx_ref, sender_id, receiver_id, category_id, amount, timestamp, description) VALUES
('MOMO20260124001', 1, 2, 2, 1100.00,  '2026-01-24 09:15:22', 'Sent to friend'),
('MOMO20260124002', 3, 1, 1, 700.00,   '2026-01-24 10:40:11', 'Airtime top up'),
('MOMO20260123003', 4, 5, 3, 9000.50,  '2026-01-23 17:22:45', 'Electricity bill'),
('MOMO20260124004', 2, 6, 4, 12000.00, '2026-01-24 13:05:59', 'Shop payment'),
('MOMO20260125005', 5, 3, 2, 5000.75,  '2026-01-25 08:17:33', 'Support transfer'),
('MOMO20260122006', 1, 7, 5, 3000.00, '2026-01-22 14:50:10', 'Remittance received'),
('MOMO20260125007', 6, 4, 6, 7000.00,  '2026-01-25 11:30:00', 'Agent cash out');

-- Assign tags to transactions
INSERT INTO transaction_labels (transaction_id, label_id) VALUES
(1, 1), (1, 2),
(3, 1), (3, 3),
(4, 1), (4, 2),
(5, 1), (5, 6),
(6, 4),
(7, 1);

-- System activity logs
INSERT INTO system_logs (tx_ref, transaction_id, log_level, message) VALUES
('MOMO20260124001', 1, 'INFO',    'Transaction parsed and inserted'),
('XYZ-invalid-01',  NULL, 'ERROR', 'Malformed phone number in SMS'),
('MOMO20260124002', 2, 'INFO',    'Airtime transaction recorded'),
('MOMO20260124008', NULL, 'WARNING','Duplicate reference detected'),
('MOMO20260123003', 3, 'INFO',    'Bill payment processed'),
('MOMO20260125005', 5, 'INFO',    'Transfer completed successfully');