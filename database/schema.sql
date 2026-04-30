CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    email VARCHAR(320) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT 1,
    last_login_at DATETIME,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);
CREATE INDEX IF NOT EXISTS ix_users_role ON users (role);

CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_admins_username ON admins (username);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    subject VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'NEEDS_ADMIN_REVIEW',
    sentiment VARCHAR(40) NOT NULL DEFAULT 'Neutral',
    intent VARCHAR(80) NOT NULL DEFAULT 'Product Inquiry',
    priority VARCHAR(40) NOT NULL DEFAULT 'Low',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    resolved_at DATETIME,
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX IF NOT EXISTS ix_tickets_user_id ON tickets (user_id);
CREATE INDEX IF NOT EXISTS ix_tickets_status ON tickets (status);
CREATE INDEX IF NOT EXISTS ix_tickets_sentiment ON tickets (sentiment);
CREATE INDEX IF NOT EXISTS ix_tickets_intent ON tickets (intent);
CREATE INDEX IF NOT EXISTS ix_tickets_priority ON tickets (priority);

CREATE TABLE IF NOT EXISTS replies (
    id INTEGER PRIMARY KEY,
    ticket_id INTEGER NOT NULL,
    admin_id INTEGER NOT NULL,
    body TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY(ticket_id) REFERENCES tickets (id),
    FOREIGN KEY(admin_id) REFERENCES admins (id)
);

CREATE INDEX IF NOT EXISTS ix_replies_ticket_id ON replies (ticket_id);
CREATE INDEX IF NOT EXISTS ix_replies_admin_id ON replies (admin_id);

CREATE TABLE IF NOT EXISTS analytics (
    id INTEGER PRIMARY KEY,
    metric_name VARCHAR(120) NOT NULL,
    metric_value FLOAT NOT NULL,
    captured_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_analytics_metric_name ON analytics (metric_name);
CREATE INDEX IF NOT EXISTS ix_analytics_captured_at ON analytics (captured_at);
