# Campaign Archive

This directory contains archived campaign CSV files that are no longer active or have been superseded by newer versions.

## Archive Policy

- **Test campaigns** that have been replaced by production versions
- **Outdated campaign configurations** no longer in use
- **Backup copies** of previous campaign states before major changes
- **Historical campaigns** kept for reference

## Current Archived Files

### Test Campaigns
- `Testv1_pmax_basic_fulltilt.csv` - Initial PMAX campaign test (basic structure)
- `Testv1.1_pmax_corrected_fulltilt.csv` - Corrected version of initial test

## Naming Convention for Archive

When archiving files, rename them to include archive date and reason:
```
[Original_Name]_[ArchiveDate]_[Reason].csv
```

Example:
```
Testv1_pmax_basic_fulltilt_2025-01-15_superseded.csv
```

## Archive Management

### When to Archive
- When a test campaign is replaced by production version
- When campaign configuration changes significantly
- When creating backup before major modifications
- When campaign is no longer needed but worth keeping for reference

### How to Archive
```bash
# From campaigns directory
mv [filename].csv campaign_archive/
```

### Archive Cleanup
- Review archive quarterly
- Remove truly obsolete files (older than 1 year) with approval
- Compress large/old files if needed
- Document removal decisions in this README

## Archive Access

- Archive files are for reference only
- Do not import archived campaigns into Google Ads
- Contact campaign manager before reusing archived configurations
- Use archived files to understand campaign evolution history
