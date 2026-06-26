-- Migration: Fix address_normalized for NULL entries and prevent future NULLs
-- Issue: 45,967 properties have NULL address_normalized from imports Oct 2025 - Apr 2026
-- Solution: Backfill NULLs and add trigger to auto-normalize on INSERT/UPDATE

-- Step 1: Create normalization function in database
CREATE OR REPLACE FUNCTION normalize_address(address TEXT) RETURNS TEXT AS $$
DECLARE
    normalized TEXT;
    words TEXT[];
    word TEXT;
    result_words TEXT[] := ARRAY[]::TEXT[];
    lower_exceptions TEXT[] := ARRAY['and', 'the', 'of', 'de', 'von', 'van', 'na', 'an'];
    upper_exceptions TEXT[] := ARRAY['Co.', 'Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford'];
BEGIN
    IF address IS NULL OR address = '' THEN
        RETURN address;
    END IF;

    normalized := TRIM(address);

    -- Basic cleanup
    normalized := REGEXP_REPLACE(normalized, '\s+', ' ', 'g');
    normalized := REGEXP_REPLACE(normalized, ',\s*,+', ',', 'g');

    -- Remove "No." prefix
    normalized := REGEXP_REPLACE(normalized, '^No\.?\s+(\d+)', '\1', 'gi');

    -- Standardize apartment/unit
    normalized := REGEXP_REPLACE(normalized, '\mApartment\M', 'Apt', 'gi');

    -- Standardize street types
    normalized := REGEXP_REPLACE(normalized, '\mSt\.?\M', 'Street', 'gi');
    normalized := REGEXP_REPLACE(normalized, '\mRd\.?\M', 'Road', 'gi');
    normalized := REGEXP_REPLACE(normalized, '\mAve?\.?\M', 'Avenue', 'gi');
    normalized := REGEXP_REPLACE(normalized, '\mDr\.?\M', 'Drive', 'gi');
    normalized := REGEXP_REPLACE(normalized, '\mCl\.?\M', 'Close', 'gi');
    normalized := REGEXP_REPLACE(normalized, '\mCt\.?\M', 'Court', 'gi');
    normalized := REGEXP_REPLACE(normalized, '\mPk\.?\M', 'Park', 'gi');
    normalized := REGEXP_REPLACE(normalized, '\mSq\.?\M', 'Square', 'gi');

    -- Clean up punctuation
    normalized := REGEXP_REPLACE(normalized, ',\s*,', ',', 'g');
    normalized := REGEXP_REPLACE(normalized, '\s+,', ',', 'g');
    normalized := REGEXP_REPLACE(normalized, ',\s+', ', ', 'g');
    normalized := TRIM(normalized, ', ');

    -- Title case with exceptions
    words := STRING_TO_ARRAY(normalized, ' ');

    FOR i IN 1..ARRAY_LENGTH(words, 1) LOOP
        word := words[i];

        IF i = 1 THEN
            -- First word: capitalize
            result_words := ARRAY_APPEND(result_words, INITCAP(word));
        ELSIF word = ANY(upper_exceptions) THEN
            -- Keep as-is for upper exceptions
            result_words := ARRAY_APPEND(result_words, word);
        ELSIF LOWER(word) = ANY(lower_exceptions) THEN
            -- Lowercase for lower exceptions
            result_words := ARRAY_APPEND(result_words, LOWER(word));
        ELSE
            -- Default: capitalize
            result_words := ARRAY_APPEND(result_words, INITCAP(word));
        END IF;
    END LOOP;

    RETURN ARRAY_TO_STRING(result_words, ' ');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Step 2: Backfill NULL address_normalized entries (in batches to avoid locks)
DO $$
DECLARE
    batch_size INT := 1000;
    updated_count INT;
    total_updated INT := 0;
BEGIN
    LOOP
        UPDATE properties
        SET address_normalized = normalize_address(address)
        WHERE id IN (
            SELECT id
            FROM properties
            WHERE address_normalized IS NULL
            LIMIT batch_size
        );

        GET DIAGNOSTICS updated_count = ROW_COUNT;
        total_updated := total_updated + updated_count;

        RAISE NOTICE 'Updated % properties (total: %)', updated_count, total_updated;

        EXIT WHEN updated_count = 0;

        -- Brief pause between batches to avoid lock contention
        PERFORM pg_sleep(0.1);
    END LOOP;

    RAISE NOTICE 'Backfill complete: % total properties updated', total_updated;
END $$;

-- Step 3: Create trigger to auto-normalize on INSERT/UPDATE
CREATE OR REPLACE FUNCTION auto_normalize_address() RETURNS TRIGGER AS $$
BEGIN
    -- Only normalize if address changed or address_normalized is NULL
    IF (TG_OP = 'INSERT') OR
       (TG_OP = 'UPDATE' AND (NEW.address IS DISTINCT FROM OLD.address OR NEW.address_normalized IS NULL)) THEN
        NEW.address_normalized := normalize_address(NEW.address);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_auto_normalize_address ON properties;
CREATE TRIGGER trigger_auto_normalize_address
    BEFORE INSERT OR UPDATE ON properties
    FOR EACH ROW
    EXECUTE FUNCTION auto_normalize_address();

-- Step 4: Verify the fix
DO $$
DECLARE
    null_count INT;
    sample_row RECORD;
BEGIN
    SELECT COUNT(*) INTO null_count
    FROM properties
    WHERE address_normalized IS NULL;

    RAISE NOTICE 'Remaining NULL address_normalized: %', null_count;

    -- Show a sample
    SELECT id, address, address_normalized INTO sample_row
    FROM properties
    WHERE address ILIKE '%19 Fairfield Road%Glasnevin%'
    ORDER BY sale_date DESC
    LIMIT 1;

    IF FOUND THEN
        RAISE NOTICE 'Sample (19 Fairfield Road): %', sample_row;
    END IF;
END $$;
