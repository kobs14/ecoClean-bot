
-- Accounts
INSERT INTO account (account_username, account_fullname, account_phone, account_password_hash, account_is_admin, account_is_employee, account_has_training, account_status)
VALUES
('john_doe', 'John Doe', '+1234567890', 'hashed_password_1', true, true, true, 'active'),
('jane_smith', 'Jane Smith', '+1987654321', 'hashed_password_2', false, true, true, 'active'),
('bob_johnson', 'Bob Johnson', '+1122334455', 'hashed_password_3', false, false, false, 'disabled'),
('alice_williams', 'Alice Williams', '+1555666777', 'hashed_password_4', true, true, false, 'active');

-- Emails
INSERT INTO email (email_account_id, email_address, email_verified)
VALUES
((SELECT account_id FROM account WHERE account_username = 'john_doe'), 'john.doe@example.com', CURRENT_TIMESTAMP),
((SELECT account_id FROM account WHERE account_username = 'john_doe'), 'john.personal@example.com', NULL),
((SELECT account_id FROM account WHERE account_username = 'jane_smith'), 'jane.smith@example.com', CURRENT_TIMESTAMP),
((SELECT account_id FROM account WHERE account_username = 'bob_johnson'), 'bob.johnson@example.com', NULL),
((SELECT account_id FROM account WHERE account_username = 'alice_williams'), 'alice.williams@example.com', CURRENT_TIMESTAMP);

