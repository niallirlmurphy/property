-- Email alerts subscription table
-- Stores user preferences for property email notifications

CREATE TABLE IF NOT EXISTS email_alerts (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    radius_km FLOAT NOT NULL DEFAULT 2.0,
    county VARCHAR(100),
    min_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_email_sent_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    unsubscribe_token UUID DEFAULT gen_random_uuid(),
    CONSTRAINT email_alerts_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Index for finding active subscriptions
CREATE INDEX IF NOT EXISTS idx_email_alerts_active ON email_alerts(is_active, last_email_sent_at);

-- Index for unsubscribe lookups
CREATE INDEX IF NOT EXISTS idx_email_alerts_unsubscribe_token ON email_alerts(unsubscribe_token);

-- Index for email lookups (prevent duplicates, manage subscriptions)
CREATE INDEX IF NOT EXISTS idx_email_alerts_email ON email_alerts(email);

COMMENT ON TABLE email_alerts IS 'User subscriptions for property email alerts';
COMMENT ON COLUMN email_alerts.email IS 'User email address';
COMMENT ON COLUMN email_alerts.address IS 'Search address/area (e.g., Dublin 2, Rathmines)';
COMMENT ON COLUMN email_alerts.radius_km IS 'Search radius in kilometers';
COMMENT ON COLUMN email_alerts.county IS 'Optional county filter';
COMMENT ON COLUMN email_alerts.min_year IS 'Optional minimum year filter';
COMMENT ON COLUMN email_alerts.last_email_sent_at IS 'When the last email was sent (null if never sent)';
COMMENT ON COLUMN email_alerts.is_active IS 'Whether subscription is active (for soft deletes/unsubscribe)';
COMMENT ON COLUMN email_alerts.unsubscribe_token IS 'Unique token for unsubscribe links';
