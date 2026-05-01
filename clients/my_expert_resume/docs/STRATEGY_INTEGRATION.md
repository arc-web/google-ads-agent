# Strategy Integration - RSA & Sitelink Guidelines

## Overview

This document outlines how comprehensive RSA (Responsive Search Ads) and Sitelink strategy guidelines have been integrated into the MyExpertResume Google Ads campaign tools.

## Integrated Strategies

### 1. RSA Strategy Integration ✅

**Source**: Comprehensive RSA strategy document for Google Ads Search campaigns

**Key Principles Integrated**:
- **Input Analysis**: Thorough extraction of business info, URLs, services, USPs, promotions, targeting
- **Two-Distinct RSA Approach**: Generate assets for two different RSAs with varying focus/emphasis
- **Strict Character Limits**: 30 chars headlines, 70-90 chars descriptions, 15 chars paths
- **Content Derivation**: All copy derived exclusively from input analysis
- **CSV Output Format**: Single-row format for Google Ads Editor import

**Implementation**:
- Created `rsa_campaign_generator.py` - Dedicated RSA campaign tool
- Updated input analysis in existing PMAX tools
- Enhanced validation for character limits

### 2. Sitelink Strategy Integration ✅

**Source**: Comprehensive sitelink extension strategy document

**Key Principles Integrated**:
- **Website Structure Analysis**: Identify distinct sections/pages beyond main landing page
- **4-6 Distinct Sitelinks**: Each pointing to different, relevant URLs
- **Updated Character Limits**: 25 chars text, 35 chars descriptions (corrected from previous 25)
- **Content Relevance**: Sitelinks must accurately reflect destination page content
- **Markdown Table Output**: Structured format for easy review

**Implementation**:
- Created `sitelink_generator.py` - Dedicated sitelink generation tool
- Updated validation in `google_ads_editor_exporter.py` (35 chars for descriptions)
- Enhanced sitelink generation in PMAX campaigns

## Tool Updates

### Updated Files

#### `google_ads_editor_exporter.py`
- ✅ **Sitelink Validation**: Updated from 25 to 35 characters for description lines
- ✅ **Structured Snippets**: Fixed to create ONE snippet with comma-separated values
- ✅ **Character Limits**: Strict enforcement across all extensions

#### `campaign_plan.py`
- ✅ **Input Analysis**: More thorough extraction of business information
- ✅ **Asset Generation**: Better value proposition integration
- ✅ **Validation**: Enhanced character limit checking

### New Tools Created

#### `rsa_campaign_generator.py`
- ✅ **RSA Focus**: Dedicated tool for Responsive Search Ads
- ✅ **Two RSA Generation**: Creates distinct ad variations
- ✅ **Strategy Compliance**: Follows all RSA guidelines

#### `sitelink_generator.py`
- ✅ **Sitelink Focus**: Dedicated sitelink extension generator
- ✅ **Website Analysis**: Identifies distinct page sections
- ✅ **Markdown Output**: Proper table formatting

## Character Limits (Strict Enforcement)

### Headlines
- **Regular Headlines**: 30 characters max
- **Long Headlines**: 30 characters max

### Descriptions
- **Ad Descriptions**: 90 characters max

### Extensions

#### Sitelinks
- **Link Text**: 25 characters max
- **Description Line 1**: 35 characters max
- **Description Line 2**: 35 characters max

#### Structured Snippets
- **Header**: 25 characters max
- **Individual Values**: 25 characters max each

#### Callouts
- **Each Callout**: 25 characters max

### Paths
- **Path 1**: 15 characters max
- **Path 2**: 15 characters max

## Validation Enhancements

### New Validation Rules
- ✅ **Sitelink Descriptions**: 35 character limit (was 25)
- ✅ **Structured Snippet Values**: Individual validation for comma-separated values
- ✅ **Zero Tolerance**: No character limit violations allowed

### Validation Messages
- Clear error messages with actual vs. limit counts
- Specific row identification for issues
- Recommendations vs. strict errors

## Usage Guidelines

### For PMAX Campaigns (Existing)
```bash
cd google_ads_agent/tools
python3 campaign_plan.py
```

### For RSA Campaigns (New)
```bash
cd google_ads_agent/tools
python3 rsa_campaign_generator.py
```

### For Sitelink Generation (New)
```bash
cd google_ads_agent/tools
python3 sitelink_generator.py
```

## Quality Assurance

### Testing Completed
- ✅ Character limit validation across all extensions
- ✅ Structured snippet format (single row with multiple values)
- ✅ Sitelink description limits (35 chars)
- ✅ Callout limits (25 chars)
- ✅ CSV generation and import compatibility

### Output Verification
- Final CSV: `campaigns/myexpertresume_test_campaign_executive.csv`
- 15 rows total (1 asset group + 4 sitelinks + 1 structured snippet + 8 callouts + 1 long headline row)
- All validation errors resolved
- Ready for Google Ads Editor import

## Strategy Compliance

Both RSA and Sitelink strategies have been fully integrated with:
- ✅ Comprehensive input analysis phases
- ✅ Strict character limit enforcement
- ✅ Proper content derivation rules
- ✅ Correct output formatting
- ✅ Policy compliance adherence

The tools now provide professional-grade Google Ads campaign generation following industry best practices and official guidelines.
