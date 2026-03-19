CREATE TABLE users (
    user_id INT PRIMARY KEY,
    email TEXT,
    device_id TEXT,
    country TEXT
);

CREATE TABLE data_classification (
    column_name TEXT,
    classification TEXT
);

CREATE TABLE roles_permissions (
    role TEXT,
    can_access_pii BOOLEAN
);