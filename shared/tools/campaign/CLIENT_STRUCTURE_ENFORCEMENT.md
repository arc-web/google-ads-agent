# Client Structure Enforcement System

## Overview

This system provides **dynamic, inference-based enforcement** of organizational patterns for client directories. It learns from existing clients and automatically validates, suggests fixes, and generates proper structures.

## Components

### 1. **Client Structure Validator** (`client_structure_validator.py`)

Validates client directories against organizational patterns and provides auto-fix capabilities.

**Features:**
- ✅ Validates required directories and files
- ✅ Checks naming conventions
- ✅ Validates file content structure
- ✅ Auto-fixes missing directories and basic files
- ✅ Provides actionable suggestions

**Usage:**
```bash
# Validate single client
python tools/campaign/client_structure_validator.py --client collab_med_spa

# Validate all clients
python tools/campaign/client_structure_validator.py --all

# Auto-fix issues
python tools/campaign/client_structure_validator.py --client collab_med_spa --fix

# Infer structure for new client
python tools/campaign/client_structure_validator.py --infer new_client_name
```

### 2. **Pattern Inference Engine** (`client_structure_inference.py`)

Learns organizational patterns from existing client directories and provides intelligent suggestions.

**Features:**
- 🧠 Learns patterns from all existing clients
- 📊 Analyzes directory structures, naming conventions, and file content
- 💡 Provides confidence-scored suggestions
- 📁 Saves learned patterns for reuse

**Usage:**
```bash
# Learn patterns from all clients
python tools/campaign/client_structure_inference.py --learn

# Analyze all clients
python tools/campaign/client_structure_inference.py --analyze

# Get suggestions for specific client
python tools/campaign/client_structure_inference.py --suggest collab_med_spa
```

### 3. **Template Generator** (`client_template_generator.py`)

Generates complete client directory structures using inferred patterns.

**Features:**
- 🎯 Creates complete directory structure
- 📝 Generates properly formatted files
- 🔄 Uses learned patterns for consistency
- ✅ Validates generated structure

**Usage:**
```bash
# Generate new client structure
python tools/campaign/client_template_generator.py --client new_client_name

# Generate with reference client
python tools/campaign/client_template_generator.py --client new_client --infer-from collab_med_spa

# Generate with additional info
python tools/campaign/client_template_generator.py --client new_client --website https://example.com --industry "Medical Services"
```

## How It Works

### Pattern Learning Process

1. **Analysis Phase**
   - Scans all existing client directories
   - Extracts directory structures, file names, and content patterns
   - Identifies common patterns and conventions

2. **Inference Phase**
   - Calculates confidence scores for each pattern
   - Identifies required vs. optional elements
   - Builds pattern database

3. **Application Phase**
   - Uses learned patterns to validate existing clients
   - Generates suggestions for improvements
   - Creates new structures following best practices

### Validation Rules

#### Required Directories
- `campaigns/` - CSV exports for Google Ads Editor
- `docs/` - Documentation and reports
- `assets/` - Campaign assets
- `search_themes/` - Search theme configurations

#### Required Files
- `README.md` - Client directory documentation
- `{client_name}_client_config.yaml` - Client configuration

#### Naming Conventions
- CSV files: `{ClientName}_{Description}_2025.csv`
- Config files: `{client_name}_client_config.yaml`
- Documentation: Standard names like `ANALYSIS_REPORT.md`, `CLIENT_SPECIFIC_IMPLEMENTATION.md`

## Integration with AI

### For AI Agents

When creating or modifying client directories, AI agents should:

1. **Before Creating:**
   ```python
   from tools.campaign.client_structure_validator import ClientStructureValidator
   from tools.campaign.client_template_generator import ClientTemplateGenerator
   
   # Generate structure
   generator = ClientTemplateGenerator()
   result = generator.generate_client_structure(
       client_name="new_client",
       website="https://example.com",
       industry="Medical Services"
   )
   ```

2. **Before Modifying:**
   ```python
   validator = ClientStructureValidator()
   issues = validator.validate_client("client_name")
   
   # Check for issues
   errors = [i for i in issues if i.severity == 'error']
   if errors:
       # Fix or report issues
       pass
   ```

3. **When Saving Files:**
   - Use inferred naming patterns
   - Follow learned directory structure
   - Validate before committing

### Inference-Based Suggestions

The system provides AI agents with:

- **Pattern Confidence Scores**: How common a pattern is across clients
- **Missing Element Detection**: What's required but missing
- **Naming Suggestions**: Proper names based on conventions
- **Content Templates**: Standard content structures

## Benefits

### 1. **Dynamic Enforcement**
- Patterns learned from actual usage
- Adapts as organization evolves
- No hardcoded rules to maintain

### 2. **Intuitive**
- Clear error messages with suggestions
- Auto-fix for common issues
- Visual validation reports

### 3. **Inference-Based**
- Learns from examples
- Provides confidence scores
- Suggests improvements proactively

### 4. **Consistent**
- All clients follow same patterns
- Reduces manual errors
- Easier to maintain

## Example Workflow

### Creating a New Client

```bash
# 1. Learn patterns from existing clients
python tools/campaign/client_structure_inference.py --learn

# 2. Generate new client structure
python tools/campaign/client_template_generator.py \
    --client new_client_name \
    --website https://example.com \
    --industry "Industry Name"

# 3. Validate generated structure
python tools/campaign/client_structure_validator.py --client new_client_name

# 4. Fix any issues
python tools/campaign/client_structure_validator.py --client new_client_name --fix
```

### Validating Existing Clients

```bash
# Check all clients
python tools/campaign/client_structure_validator.py --all --output validation_report.json

# Get suggestions for specific client
python tools/campaign/client_structure_inference.py --suggest collab_med_spa
```

## Future Enhancements

### Planned Features

1. **AI Integration**
   - Direct integration with AI agents
   - Automatic pattern learning from AI actions
   - Proactive suggestions during file creation

2. **Real-time Validation**
   - Git hooks for pre-commit validation
   - IDE integration for live feedback
   - Continuous pattern learning

3. **Advanced Inference**
   - Machine learning for pattern detection
   - Industry-specific pattern recognition
   - Predictive structure suggestions

4. **Configuration-Driven**
   - YAML configuration for custom rules
   - Per-client pattern overrides
   - Team-specific conventions

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'yaml'`
**Solution**: Install PyYAML: `pip install pyyaml`

**Issue**: Patterns not learning correctly
**Solution**: Run `--learn` command to rebuild pattern database

**Issue**: Validation finds false positives
**Solution**: Check pattern confidence scores, adjust thresholds if needed

## Contributing

When adding new organizational patterns:

1. Update validation rules in `client_structure_validator.py`
2. Add pattern extraction logic in `client_structure_inference.py`
3. Update templates in `client_template_generator.py`
4. Test with existing clients
5. Document new patterns in this file
