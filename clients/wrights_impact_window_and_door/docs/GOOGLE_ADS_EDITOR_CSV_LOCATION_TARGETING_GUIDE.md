# Google Ads Editor CSV Location Targeting Configuration Guide

## Overview
This guide provides comprehensive information on configuring regional targeting in Google Ads Editor CSV imports/exports, based on official Google Ads Editor documentation and API specifications.

## Core Location Targeting CSV Columns

### Primary Location Columns

#### 1. **Location Name** (Required)
- **Description**: The display name of the location target
- **Format**: Free text, but should match Google's location database
- **Examples**:
  - `Fort Lauderdale, FL`
  - `Broward County, FL`
  - `33432, FL` (ZIP code)
  - `United States`

#### 2. **Location Type** (Required)
- **Description**: Specifies the type of geographic targeting
- **Valid Values**:
  - `Country`
  - `State`
  - `City`
  - `County`
  - `ZIP`
  - `DMA` (Designated Market Area)
  - `Proximity` (Radius targeting)

#### 3. **Location Status** (Optional)
- **Description**: Current status of the location target
- **Valid Values**:
  - `Enabled` (default)
  - `Removed`

#### 4. **Is Negative** (Required for Exclusions)
- **Description**: Whether this location should be excluded
- **Valid Values**:
  - `TRUE` (exclude this location)
  - `FALSE` or blank (include this location)
- **Usage**: Set to `TRUE` for geographic exclusions

### Advanced Location Columns

#### 5. **Bid Modifier** (Optional)
- **Description**: Percentage bid adjustment for this location
- **Format**: Decimal between -0.9 and 9.0
- **Examples**:
  - `0.2` (20% increase)
  - `-0.5` (50% decrease)
- **Note**: Only applies to locations with better performance data

#### 6. **Proximity Target** (For Radius Targeting)
- **Description**: Address or coordinates for radius-based targeting
- **Format**: Street address or latitude,longitude
- **Examples**:
  - `123 Main St, Fort Lauderdale, FL 33301`
  - `26.1224,-80.1373` (coordinates)

#### 7. **Radius** (For Radius Targeting)
- **Description**: Distance from proximity target
- **Format**: Numeric value
- **Unit**: Determined by Radius Unit column

#### 8. **Radius Unit** (For Radius Targeting)
- **Description**: Unit of measurement for radius
- **Valid Values**:
  - `Miles`
  - `Kilometers`

### Geographic Detail Columns

#### 9. **Address** (Optional)
- **Description**: Full street address for precise targeting
- **Format**: Complete address including street, city, state, ZIP

#### 10. **ZIP** (For ZIP Code Targeting)
- **Description**: 5-digit or 9-digit ZIP code
- **Format**: `12345` or `12345-6789`

#### 11. **City** (Optional)
- **Description**: City name for city-level targeting
- **Format**: Full city name

#### 12. **State** (Optional)
- **Description**: State or province code
- **Format**: 2-letter state code (e.g., `FL`, `CA`)

#### 13. **Country** (Required for International)
- **Description**: Country code
- **Format**: 2-letter country code (e.g., `US`, `CA`)
- **Default**: `US` for domestic campaigns

## CSV Import/Export Structure

### Required Columns for Location Targeting
```csv
Account,Campaign,Location Name,Location Type,Is Negative
```

### Complete Location Targeting Row Example
```csv
My Account,My Campaign,Fort Lauderdale, FL,City,FALSE
My Account,My Campaign,Broward County, FL,County,FALSE
My Account,My Campaign,33432, FL,ZIP,FALSE
My Account,My Campaign,Miami, FL,City,TRUE
```

### Bulk Location Import Format
```csv
Account,Campaign,Location Name,Location Type,Is Negative,Bid Modifier
My Account,Broward Campaign,"Fort Lauderdale, FL",City,FALSE,0.2
My Account,Broward Campaign,"Hollywood, FL",City,FALSE,0.1
My Account,Broward Campaign,"Pembroke Pines, FL",City,FALSE,0.15
My Account,Broward Campaign,"Coral Springs, FL",City,FALSE,0.1
```

## Location Targeting Best Practices

### 1. **Multi-Level Targeting**
```csv
Account,Campaign,Location Name,Location Type,Is Negative
My Account,Regional Campaign,Broward County, FL,County,FALSE
My Account,Regional Campaign,Fort Lauderdale, FL,City,FALSE
My Account,Regional Campaign,33301, FL,ZIP,FALSE
```

### 2. **ZIP Code Bulk Import**
```csv
Account,Campaign,Location Name,Location Type,Is Negative
My Account,ZIP Campaign,33301, FL,ZIP,FALSE
My Account,ZIP Campaign,33304, FL,ZIP,FALSE
My Account,ZIP Campaign,33305, FL,ZIP,FALSE
My Account,ZIP Campaign,33308, FL,ZIP,FALSE
```

### 3. **Exclusion Setup**
```csv
Account,Campaign,Location Name,Location Type,Is Negative
My Account,Targeted Campaign,Miami-Dade County, FL,County,TRUE
My Account,Targeted Campaign,Broward County, FL,County,FALSE
```

### 4. **Radius Targeting**
```csv
Account,Campaign,Location Name,Location Type,Is Negative,Proximity Target,Radius,Radius Unit
My Account,Local Campaign,Radius Target,Proximity,FALSE,"123 Main St, Fort Lauderdale, FL 33301",25,Miles
```

## Export Format Analysis

When exporting from Google Ads Editor, location data appears in these columns:

### Campaign-Level Export
```csv
Campaign,Location,Bid Modifier
My Campaign,"Fort Lauderdale, FL; Broward County, FL",0.2
```

### Location-Specific Export
```csv
Campaign,Location Name,Location Type,Location Status,Is Negative,Bid Modifier
My Campaign,"Fort Lauderdale, FL",City,Enabled,FALSE,0.2
```

## Common Issues & Solutions

### Issue 1: Location Not Found
**Error**: "Location name not recognized"
**Solution**: Use exact Google location names or canonical IDs

### Issue 2: Invalid ZIP Code Format
**Error**: "Invalid ZIP code"
**Solution**: Use 5-digit format (e.g., `33301`) without quotes

### Issue 3: Conflicting Targeting
**Error**: "Cannot target and exclude same location"
**Solution**: Remove conflicting location entries

### Issue 4: Bid Modifier Range Error
**Error**: "Bid modifier out of range"
**Solution**: Keep between -0.9 and 9.0

## Advanced Configuration

### Regional Performance Targeting
```csv
Account,Campaign,Location Name,Location Type,Is Negative,Bid Modifier,Performance Notes
My Account,Optimized Campaign,"Fort Lauderdale, FL",City,FALSE,0.3,"High conversion area"
My Account,Optimized Campaign,"Pompano Beach, FL",City,FALSE,0.1,"Medium performance"
```

### Seasonal Targeting Adjustments
```csv
Account,Campaign,Location Name,Location Type,Is Negative,Bid Modifier,Season
My Account,Hurricane Campaign,"Broward County, FL",County,FALSE,0.5,"June-November"
```

## Integration with Campaign Structure

### Linking to Campaign Rows
```csv
Account,Campaign,Campaign Type,Location,Budget
My Account,Broward Search,Search,"Fort Lauderdale, FL; Broward County, FL",500.00
```

### Ad Group Level Targeting
```csv
Account,Campaign,Ad Group,Location Name,Location Type
My Account,Broward Campaign,Windows Ad Group,"Fort Lauderdale, FL",City
```

## Validation Checklist

- [ ] Location Name matches Google's database exactly
- [ ] Location Type is valid enum value
- [ ] Is Negative is TRUE/FALSE or blank
- [ ] ZIP codes are 5-digit format
- [ ] Bid modifiers within -0.9 to 9.0 range
- [ ] No conflicting include/exclude rules
- [ ] Account column matches account name
- [ ] Campaign column matches existing campaign

## API Integration Notes

For automated imports, the Google Ads API uses:
- `CampaignCriterion` with `Location` criterion type
- `GeoTargetConstant` resource for location IDs
- `LocationInfo` for proximity targeting

This CSV format provides direct mapping to API calls for bulk operations.