INSERT INTO users VALUES
(101, 'alice@example.com', 'dev_abc', 'US'),
(102, 'bob@example.com', 'dev_xyz', 'CA'),
(103, 'carol@example.com', 'dev_123', 'US');

INSERT INTO data_classification VALUES
('email', 'PII'),
('device_id', 'PII'),
('user_id', 'PII'),
('campaign_id', 'SAFE'),
('clicked', 'SAFE');

INSERT INTO roles_permissions VALUES
('marketing_analyst', false),
('data_scientist', true);