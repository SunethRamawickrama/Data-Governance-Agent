INSERT INTO campaigns (name, budget, start_date, end_date) VALUES
('iPhone Launch', 100000, '2025-01-01', '2025-03-01'),
('MacBook Campaign', 80000, '2025-02-01', '2025-04-01');

INSERT INTO ad_clicks (campaign_id, user_id, device_id, country, clicked, timestamp) VALUES
(1, 101, 'dev_abc', 'US', true, NOW()),
(1, 102, 'dev_xyz', 'CA', false, NOW()),
(2, 103, 'dev_123', 'US', true, NOW());