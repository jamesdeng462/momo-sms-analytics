-- Create application user with least privileges
CREATE USER 'momo_api'@'localhost' IDENTIFIED BY 'SecurePass123!';
GRANT SELECT, INSERT, UPDATE, DELETE ON momo_sms_db.* TO 'momo_api'@'localhost';

-- Create read-only user for reporting
CREATE USER 'momo_readonly'@'localhost' IDENTIFIED BY 'ReadOnly456!';
GRANT SELECT ON momo_sms_db.* TO 'momo_readonly'@'localhost';