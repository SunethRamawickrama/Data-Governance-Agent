CREATE TABLE campaigns (
    campaign_id SERIAL PRIMARY KEY,
    name TEXT,
    budget FLOAT,
    start_date DATE,
    end_date DATE
);

CREATE TABLE ad_clicks (
    click_id SERIAL PRIMARY KEY,
    campaign_id INT,
    user_id INT,
    device_id TEXT,
    country TEXT,
    clicked BOOLEAN,
    timestamp TIMESTAMP
);