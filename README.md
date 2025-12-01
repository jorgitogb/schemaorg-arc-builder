# Schema.org to ISA RO-Crate Parser

Parse Schema.org JSON-LD metadata into ISA (Investigation/Study/Assay) RO-Crate structure.

## Overview

This tool converts Schema.org metadata (in JSON-LD format) into RO-Crate following the ISA model. It handles various JSON-LD structures that can represent the same information and normalizes them into a consistent RO-Crate format.

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
python main.py examples/example_edal.json -o output-crate
```

Output JSON-LD to stdout:

```bash
python main.py examples/example_bonares.json --json
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

## Output

The parser generates an RO-Crate directory with:
- `ro-crate-metadata.json`: The RO-Crate metadata file
- Properly structured entities following ISA patterns

## Development

Project structure:

```
schemaorg_rocrate_parser/
├── __init__.py           # Package exports
├── parser.py             # JSON-LD parser
└── rocrate_builder.py    # RO-Crate builder
```

## Requirements

- Python >= 3.13
- rocrate >= 0.10.0
- rdflib >= 7.0.0
- pyld >= 2.0.0

## License

[Add your license here]
