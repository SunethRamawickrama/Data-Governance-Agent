CREATE TABLE data_sources (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(255) NOT NULL, 
    source_type   VARCHAR(50) NOT NULL,    
    host          VARCHAR(255),           
    port          INTEGER,                 
    source_name VARCHAR(255),
    status        VARCHAR(50) DEFAULT 'active',
    last_ping     TIMESTAMP,
    metadata      JSONB,                 
    created_at    TIMESTAMP DEFAULT now()
);