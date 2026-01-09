
# GOOGLE ADS EDITOR WORKFLOW - Wright's Search Campaigns

## CSV UPLOAD PROCEDURE

### Step 1: Prepare CSV File
- [ ] File named: Wrights_Search_Campaigns_2026.csv
- [ ] UTF-8 encoding (no BOM)
- [ ] No empty rows at end
- [ ] Headers match Google Ads Editor format exactly

### Step 2: Open Google Ads Editor
- [ ] Launch Google Ads Editor application
- [ ] Sign in to correct Google Ads account
- [ ] Verify account selection (Wright's account)

### Step 3: Import CSV
1. Click "File" > "Import" > "CSV file"
2. Select Wrights_Search_Campaigns_2026.csv
3. Choose import options:
   - [ ] Update existing campaigns/ad groups
   - [ ] Create new campaigns/ad groups
   - [ ] Update keywords and ads
4. Click "Import"

### Step 4: Review Import Results
- [ ] Check "Import Summary" for errors
- [ ] Review "Changes" tab for modifications
- [ ] Verify no validation errors
- [ ] Check "Errors" tab for issues

### Step 5: Post-Upload Validation
- [ ] Click "Get recent changes" to sync
- [ ] Verify campaigns appear in account
- [ ] Check asset group creation
- [ ] Confirm bid strategies applied correctly
- [ ] Validate geographic targeting

## ERROR HANDLING PROCEDURES

### Common Errors and Fixes:

#### "Invalid bid strategy"
**Cause**: Asset group strategy incompatible with campaign
**Fix**: Ensure campaign uses Manual CPC, asset groups use specific strategies

#### "Character limit exceeded"
**Cause**: Campaign/asset group names too long
**Fix**: Use abbreviated names (see naming conventions)

#### "Invalid geographic targeting"
**Cause**: ZIP code format incorrect
**Fix**: Use exact format: "City, FL - ZIP codes: ZIP1, ZIP2..."

#### "Conversion action not found"
**Cause**: Conversion tracking not set up
**Fix**: Create conversion actions before upload (see setup guide)

#### "Negative keywords conflict"
**Cause**: Duplicate or conflicting negatives
**Fix**: Remove duplicates, ensure proper match types

### Rollback Procedures:
1. **If major errors**: Don't publish changes
2. **Click "Undo all changes"** to revert
3. **Fix CSV file** with corrected data
4. **Re-import** corrected CSV
5. **Verify** before publishing

## BULK EDIT TECHNIQUES

### Editing Multiple Asset Groups:
1. Select multiple asset groups (Ctrl+click)
2. Right-click > "Edit" > "Change bid strategies"
3. Apply changes in bulk
4. Verify changes applied correctly

### Bulk Geographic Updates:
1. Select asset groups for same city
2. Edit geographic targeting
3. Apply same ZIP code list
4. Check targeting accuracy

### Bulk Keyword Management:
1. Export existing keywords
2. Edit CSV with new keywords
3. Import updated keyword CSV
4. Verify keyword associations

## VALIDATION CHECKLISTS

### Pre-Upload Checklist:
- [ ] CSV file properly formatted
- [ ] All required columns present
- [ ] Character limits respected
- [ ] Bid strategies correctly specified
- [ ] Geographic targeting validated
- [ ] Conversion actions exist

### Post-Upload Checklist:
- [ ] All campaigns created
- [ ] Asset groups populated
- [ ] Bid strategies applied
- [ ] Keywords uploaded
- [ ] Geographic targeting active
- [ ] No error messages

### Final Verification:
- [ ] Preview ads for each asset group
- [ ] Check bid strategy settings
- [ ] Verify geographic coverage
- [ ] Test conversion tracking
- [ ] Confirm negative keywords applied
