# Regional Targeting Configuration - Google Ads Editor CSV Implementation

## 📋 Complete Information from Context7 Research

Based on comprehensive research using Context7 across Google Ads API documentation, Google Ads Scripts, and Google Ads Editor support resources, here's the definitive guide for regional targeting configuration in Google Ads Editor CSV imports/exports.

## 🎯 Key Findings from Context7

### Google Ads API Location Targeting
- **SuggestGeoTargetConstants API**: Programmatic endpoint for location suggestions
- **Supported Methods**: REST API, gRPC, client libraries (Python, Java, PHP, .NET, Ruby)
- **Location Types**: Country, State, City, County, ZIP, DMA, Proximity
- **Response Format**: Includes reach estimates, locale matching, search terms

### Google Ads Scripts Bulk Upload
- **CSV Upload Methods**: `newCsvUpload()` with column headers
- **Money Formatting**: Supports micros (1370000) or currency (1.37)
- **Date/Time Zone**: Configurable locale and timezone parsing
- **File Paths**: Supports relative paths for asset imports

### Google Ads Editor CSV Structure
- **Column Separation**: Semicolon for multi-value fields
- **Header Requirements**: First row must contain column headers
- **Entity Per Row**: Each row represents one entity (campaign, ad group, location)
- **Import Validation**: Google Ads Editor validates against account structure

## 📊 Google Ads Editor CSV Location Targeting Columns

### Required Columns for Location Targeting
```csv
Account,Campaign,Location Name,Location Type,Is Negative
```

### Complete Column Set (from Google Ads Editor exports)
```
Account,Campaign,Location Name,Location Type,Location Status,Is Negative,Bid Modifier,Proximity Target,Radius,Radius Unit,Address,ZIP,City,State,Country
```

### Column Definitions & Formats

#### Core Location Columns
- **Account**: Account name (matches Google Ads account)
- **Campaign**: Campaign name (must exist or be created)
- **Location Name**: Geographic target name (e.g., "Fort Lauderdale, FL")
- **Location Type**: `Country|State|City|County|ZIP|DMA|Proximity`
- **Is Negative**: `TRUE` for exclusions, `FALSE` or blank for inclusions

#### Advanced Targeting Columns
- **Location Status**: `Enabled|Removed` (current status)
- **Bid Modifier**: `-0.9 to 9.0` (percentage adjustment)
- **Proximity Target**: Address or coordinates for radius targeting
- **Radius**: Numeric distance value
- **Radius Unit**: `Miles|Kilometers`
- **Address**: Full street address
- **ZIP**: 5-digit ZIP code (e.g., `33301`)
- **City**: City name
- **State**: 2-letter state code
- **Country**: 2-letter country code (usually `US`)

## 🚀 Implementation Examples

### 1. City-Level Targeting
```csv
Account,Campaign,Location Name,Location Type,Is Negative,Bid Modifier
Wright's Impact Window and Door,Broward Campaign,"Fort Lauderdale, FL",City,FALSE,0.2
Wright's Impact Window and Door,Broward Campaign,"Hollywood, FL",City,FALSE,0.15
```

### 2. ZIP Code Targeting
```csv
Account,Campaign,Location Name,Location Type,Is Negative,Bid Modifier
Wright's Impact Window and Door,ZIP Campaign,33301, FL,ZIP,FALSE,0.3
Wright's Impact Window and Door,ZIP Campaign,33019, FL,ZIP,FALSE,0.2
```

### 3. Exclusion Setup
```csv
Account,Campaign,Location Name,Location Type,Is Negative
Wright's Impact Window and Door,Targeted Campaign,"Miami-Dade County, FL",County,TRUE
```

### 4. Radius Targeting
```csv
Account,Campaign,Location Name,Location Type,Is Negative,Proximity Target,Radius,Radius Unit
Wright's Impact Window and Door,Local Campaign,Radius Target,Proximity,FALSE,"123 Main St, Fort Lauderdale, FL 33301",25,Miles
```

## 📈 Bulk Import Strategies

### Regional Rollout Approach
1. **County Level**: Establish broad coverage
2. **City Level**: Add precision targeting
3. **ZIP Level**: Implement granular control
4. **Exclusion Layer**: Remove unwanted areas

### Performance-Based Bid Adjustments
```csv
Account,Campaign,Location Name,Location Type,Is Negative,Bid Modifier,Performance Notes
Wright's Impact Window and Door,Optimized Campaign,"Fort Lauderdale, FL",City,FALSE,0.3,"High conversion area - 25% above average"
Wright's Impact Window and Door,Optimized Campaign,"Coral Springs, FL",City,FALSE,-0.2,"Underperforming - reduce bids by 20%"
```

## ⚠️ Critical Validation Rules

### Format Requirements
- **Location Name**: Must match Google's location database exactly
- **ZIP Codes**: 5-digit format only (no quotes, no extensions)
- **Bid Modifiers**: Decimal format between -0.9 and 9.0
- **Boolean Fields**: `TRUE` or `FALSE` (case sensitive)
- **Multi-Value**: Semicolon separated (e.g., `en;es`)

### Common Errors & Solutions
1. **"Location not found"**: Use canonical Google location names
2. **"Invalid ZIP"**: Ensure 5-digit format without quotes
3. **"Bid modifier range"**: Keep within -0.9 to 9.0
4. **"Conflicting targets"**: Cannot include and exclude same location

## 🔗 Integration Points

### Campaign-Level Location Settings
```csv
Account,Campaign,Campaign Type,Location,Budget
Wright's Impact Window and Door,Broward Search,Search,"Fort Lauderdale, FL; Broward County, FL",500.00
```

### Ad Group-Level Targeting
```csv
Account,Campaign,Ad Group,Location Name,Location Type
Wright's Impact Window and Door,Broward Campaign,Windows Ad Group,"Fort Lauderdale, FL",City
```

### Export Format Analysis
When exporting, Google Ads Editor combines locations:
```csv
Campaign,Location,Bid Modifier
My Campaign,"Fort Lauderdale, FL; Broward County, FL; 33301, FL",0.2
```

## 📚 Source Documentation

**Primary Sources from Context7:**
1. **Google Ads API Documentation** (`/websites/developers_google_com-google-ads-api-docs`)
   - 54,803 code snippets
   - Complete API reference for location targeting

2. **Google Ads Scripts** (`/websites/developers_google_google-ads_scripts`)
   - Bulk upload methods
   - CSV processing examples
   - 48,382 code snippets

3. **Google Ads Editor Support** (`/websites/support_google_google-ads_editor`)
   - CSV format specifications
   - Import/export procedures
   - 613 code snippets

## 🎯 Ready-to-Implement Broward County Examples

See attached files:
- `BROWARD_COUNTY_LOCATION_TARGETING_EXAMPLE.csv` - City-level targeting
- `BROWARD_COUNTY_ZIP_TARGETING_EXAMPLE.csv` - Complete ZIP code coverage
- `GOOGLE_ADS_EDITOR_CSV_LOCATION_TARGETING_GUIDE.md` - Comprehensive documentation

## ✅ Validation Checklist

- [ ] Account name matches Google Ads account exactly
- [ ] Campaign names exist or will be created
- [ ] Location names use Google's canonical format
- [ ] Location types are valid enum values
- [ ] ZIP codes are 5-digit format
- [ ] Bid modifiers within acceptable range
- [ ] No conflicting include/exclude rules
- [ ] CSV encoding is UTF-8
- [ ] No special characters in location names

This comprehensive guide provides everything needed for proper regional targeting configuration in Google Ads Editor CSV imports/exports, based on official Google documentation and API specifications.