
# ZIP CODE TARGETING PROCEDURES - Wright's Search Campaigns

## ZIP CODE REQUIREMENTS BY CITY

### Fort Myers Area:
```
33901, 33902, 33903, 33905, 33906, 33907, 33908, 33912, 33913, 33916, 33917, 33919, 33921, 33922, 33924, 33931, 33932, 33936, 33956, 33957, 33965, 33966, 33967, 33971, 33972, 33973, 33976, 33990, 33991, 33993, 33994
```

### Cape Coral Area:
```
33904, 33909, 33914, 33915, 33921
```

### Naples Area:
```
34101, 34102, 34103, 34104, 34105, 34106, 34107, 34108, 34109, 34110, 34112, 34113, 34114, 34116, 34117, 34119, 34120, 34133, 34134, 34135, 34136, 34137, 34138, 34139, 34140, 34141, 34142, 34143, 34145, 34146
```

### Fort Lauderdale Area:
```
33301, 33302, 33303, 33304, 33305, 33306, 33307, 33308, 33309, 33310, 33311, 33312, 33313, 33314, 33315, 33316, 33317, 33318, 33319, 33320, 33321, 33322, 33323, 33324, 33325, 33326, 33327, 33328, 33330, 33331, 33332, 33334, 33351
```

### Pompano Beach Area:
```
33060, 33061, 33062, 33063, 33064, 33065, 33066, 33067, 33068, 33069, 33071, 33073, 33074, 33076, 33077
```

### Hollywood Area:
```
33004, 33009, 33019, 33020, 33021, 33022, 33023, 33024, 33025, 33026, 33027, 33028, 33029, 33081, 33083, 33084
```

## ZIP CODE VALIDATION PROCEDURES

### CSV Format Requirements:
```
Geographic Targeting Column Format:
"City Name, FL - ZIP codes: ZIP1, ZIP2, ZIP3..."
```

### Example CSV Entry:
```
Geographic Targeting: "Fort Myers, FL - ZIP codes: 33901, 33902, 33903, 33905, 33906..."
```

### Validation Checklist:
- [ ] All ZIP codes are 5 digits
- [ ] ZIP codes are Florida codes (33XXX or 34XXX)
- [ ] No duplicate ZIP codes within same targeting
- [ ] ZIP codes match actual service areas
- [ ] Geographic targeting format matches Google Ads requirements

## TARGETING COMPLEXITY MANAGEMENT

### Maximum ZIP Codes Per Asset Group:
- Google Ads limit: No specific limit, but recommend < 50 per group
- Current setup: Fort Myers has 27 ZIP codes (within limit)

### Geographic Overlap Prevention:
- Each ZIP code assigned to only one asset group
- No ZIP code appears in multiple city targeting
- Clear geographic boundaries maintained

### Targeting Verification:
- Use Google Ads preview tool to verify targeting accuracy
- Check that ads show for intended ZIP codes only
- Monitor for unintended geographic coverage
