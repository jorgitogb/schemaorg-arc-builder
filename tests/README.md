# Tests

This directory contains testing and debugging utilities.

## Files

- **check_xlsx.py**: Verify Excel file content and structure
- **inspect_investigation.py**: Detailed inspection of investigation Excel files
- **list_projects.py**: List GitLab projects in a namespace

## Usage

### Check Excel file
```bash
uv run python tests/check_xlsx.py path/to/file.xlsx
```

### Inspect investigation file
```bash
uv run python tests/inspect_investigation.py path/to/isa.investigation.xlsx
```
