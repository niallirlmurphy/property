# Salesforce Custom Field Setup

## Create PPR_Import__c Field on Account

This field will mark all records imported from Property Price Register data, making them easy to identify and clean up.

### Steps to Create Field (2 minutes)

1. **Log into Salesforce** at https://login.salesforce.com

2. **Navigate to Object Manager**
   - Click the gear icon (⚙️) in top right
   - Click "Setup"
   - In Quick Find box, type "Object Manager"
   - Click "Object Manager"

3. **Open Account Object**
   - Find and click "Account" in the list

4. **Create New Field**
   - Click "Fields & Relationships" in left sidebar
   - Click "New" button

5. **Field Configuration**
   - Step 1: Data Type
     - Select: **Checkbox**
     - Click "Next"
   
   - Step 2: Field Details
     - Field Label: `PPR Import`
     - Field Name: `PPR_Import` (auto-filled)
     - Default Value: **Unchecked**
     - Description: `Marks records imported from Property Price Register data`
     - Help Text: (leave blank)
     - Click "Next"
   
   - Step 3: Field-Level Security
     - Check "Visible" for all profiles
     - Click "Next"
   
   - Step 4: Page Layouts
     - Check all page layouts (field will be visible)
     - Click "Save"

6. **Verify**
   - You should see `PPR Import` in the custom fields list
   - API Name: `PPR_Import__c`

## Once Field is Created

Run this command to verify:

```bash
sf data query --query "DESCRIBE Account" | grep PPR_Import
```

Or test with:

```bash
python3 scripts/test_salesforce_field.py
```

## Why This Field?

- **Easy identification**: All PPR imported records have `PPR_Import__c = true`
- **Easy cleanup**: Delete all records where `PPR_Import__c = true`
- **No interference**: Existing Salesforce data remains untouched
- **Bulk operations**: Can filter on this field for mass updates/deletes

## Cleanup Query (Once Imports Start)

```sql
-- Count PPR imported records
SELECT COUNT() FROM Account WHERE PPR_Import__c = true

-- Delete all PPR imported records
DELETE FROM Account WHERE PPR_Import__c = true
```

## Alternative Approach (If Field Can't Be Created)

If you can't create custom fields, we can:
1. Use Account Description field to mark records
2. Use a specific Account naming pattern (e.g., prefix with "PPR:")
3. Use a separate Account Type for PPR data

Let me know which approach you prefer!
