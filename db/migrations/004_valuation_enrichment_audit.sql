-- Audit trail for details users enter on the valuation page (bedrooms, Eircode, BER)
-- that are written back to properties (backend/valuation/api.py::enrich_property_from_request).

-- Where a property's bedrooms came from: 'valuation_request' (entered by a user on the
-- valuation page) or NULL (legacy / web enrichment).
ALTER TABLE properties ADD COLUMN IF NOT EXISTS bedrooms_source TEXT;

-- Which property rows (one per sale of the house) a valuation request filled in.
ALTER TABLE valuation_requests ADD COLUMN IF NOT EXISTS enriched_property_ids BIGINT[];
