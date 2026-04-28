# Schema.org to ISA RO-Crate Parser

Parse Schema.org JSON-LD metadata into ISA (Investigation/Study/Assay) RO-Crate structure and submit to GitLab as ARC repositories.

## Overview

This tool converts Schema.org metadata (in JSON-LD format) into RO-Crate following the ISA model, generates ARCs (Annotated Research Contexts) using ARCtrl, and can submit them to GitLab repositories. It handles various JSON-LD structures that can represent the same information and normalizes them into a consistent RO-Crate format.

## Features

- **Flexible JSON-LD parsing**: Handles different JSON-LD structures:
  - Single entities
  - Arrays of entities
  - Named graphs (`@graph`)
  - Various Schema.org types (Dataset, Person, Organization, ScholarlyArticle, etc.)

- **ISA RO-Crate generation**: Creates Research Object Crates following ISA patterns
  
- **Entity mapping**: Automatically maps Schema.org types to RO-Crate entities:
  - `Dataset` → Investigation/Study
  - `Person` → Person entities with affiliations
  - `Organization` → Organization entities
  - `ScholarlyArticle` → Publication references

## Installation

Install dependencies using `uv`:

```bash
uv sync
```

Or using pip:

```bash
pip install -e .
```

## Usage

### Command Line

Parse a JSON-LD file and create an RO-Crate:

```bash
schemaorg-rocrate-parser examples/edal.json -o output-crate
```

Output JSON-LD to stdout:

```bash
schemaorg-rocrate-parser examples/bonares.json --json
```

### Python API

```python
from schemaorg_rocrate_parser import SchemaOrgParser, ISAROCrateBuilder

# Parse Schema.org JSON-LD
parser = SchemaOrgParser()
parsed_data = parser.parse_file("metadata.jsonld")

# Build RO-Crate
builder = ISAROCrateBuilder()
crate = builder.build_from_parsed_data(parsed_data)

# Save to disk
builder.save("my-rocrate")

# Or get as JSON-LD
json_ld = builder.to_json()
```

## Input Format Examples

### Single Dataset

```json
{
  "@context": "https://schema.org",
  "@type": "Dataset",
  "name": "My Research Dataset",
  "description": "A comprehensive study",
  "author": {
    "@type": "Person",
    "name": "Jane Doe",
    "email": "jane@example.com"
  }
}
```

### Graph Structure

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@id": "#dataset1",
      "@type": "Dataset",
      "name": "My Dataset",
      "author": {"@id": "#person1"}
    },
    {
      "@id": "#person1",
      "@type": "Person",
      "name": "Jane Doe"
    }
  ]
}
```

## ARC Generation

Generate an ARC from the RO-Crate:

```bash
python scripts/arc_creator.py output_crates/edal_arc/ro-crate-metadata.json
```

This creates:

- `arc/isa.investigation.xlsx` - Investigation Excel file
- `arc/studies/` - Study directories
- `arc/assays/` - Assay directories
- `arc/arc_structure.json` - ARC structure metadata

## GitLab Submission

### Setup Credentials

1. Create a `.env` file (never commit this!):

```bash
cp .env.example .env
```

1. Edit `.env` with your GitLab credentials:

```env
GITLAB_URL=https://your-gitlab-instance.com
GITLAB_PRIVATE_TOKEN=your-private-token
GITLAB_NAMESPACE_ID=55
GITLAB_GROUP_ID=55
```

### Submit ARC to GitLab

```bash
# Submit an ARC to GitLab
python scripts/gitlab_submit.py output_crates/edal_arc/arc --name my-arc-project

# Overwrite existing project
python scripts/gitlab_submit.py output_crates/edal_arc/arc --name my-arc-project --overwrite

# Add description
python scripts/gitlab_submit.py output_crates/edal_arc/arc \
  --name my-arc-project \
  --description "Rice genome dataset ARC"
```

### Python API for GitLab

```python
from schemaorg_rocrate_parser import GitLabSubmitter
from pathlib import Path

# Initialize with credentials from .env
submitter = GitLabSubmitter()

# Submit ARC
project = submitter.submit_arc(
    arc_directory=Path("output_crates/edal_arc/arc"),
    project_name="my-arc-project",
    description="My research ARC",
    overwrite=True
)

print(f"ARC submitted: {project['web_url']}")
```

## Output

The parser generates an RO-Crate directory with:

- `ro-crate-metadata.json`: The RO-Crate metadata file
- Properly structured entities following ISA patterns

## Development

Project structure:

```text
schemaorg_rocrate_parser/
├── schemaorg_rocrate_parser/
│   ├── __init__.py           # Package exports
│   ├── __main__.py           # CLI entry point
│   ├── parser.py             # JSON-LD parser
│   └── rocrate_builder.py    # RO-Crate builder
├── scripts/
│   ├── arc_creator.py       # ARC creation from RO-Crate
│   ├── gitlab_submitter.py  # GitLab push
│   └── gitlab_submit.py     # CLI wrapper
├── examples/                 # JSON-LD input examples
├── tests/                    # pytest suite
└── pyproject.toml
```

## Requirements

- Python >= 3.13
- rocrate >= 0.10.0
- rdflib >= 7.0.0
- pyld >= 2.0.0

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
