-- '1.2.1-ladder-bedmatch' is 21 characters: every successful valuation since that
-- version shipped (~2026-10-17) failed to insert into valuation_requests.
ALTER TABLE valuation_requests ALTER COLUMN algorithm_version TYPE VARCHAR(50);
