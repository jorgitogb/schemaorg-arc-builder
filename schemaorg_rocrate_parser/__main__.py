"""Schema.org to ISA RO-Crate Parser - Main Entry Point."""

import argparse
import json
import sys
from pathlib import Path

from schemaorg_rocrate_parser import ISAROCrateBuilder, SchemaOrgParser


def main():
    """Parse Schema.org JSON-LD metadata and convert to ISA RO-Crate."""
    parser = argparse.ArgumentParser(
        description="Parse Schema.org JSON-LD metadata into ISA RO-Crate structure"
    )
    parser.add_argument(
        "input",
        type=str,
        help="Path to input JSON-LD file containing Schema.org metadata"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="ro-crate",
        help="Output directory for RO-Crate (default: ro-crate)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON-LD to stdout instead of writing to disk"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Parse Schema.org JSON-LD
        print(f"Parsing Schema.org metadata from: {args.input}")
        schemaorg_parser = SchemaOrgParser()
        parsed_data = schemaorg_parser.parse_file(input_path)
        
        # Debug: show parsed data
        # print(f"DEBUG - Parsed data: {json.dumps(parsed_data, indent=2)}")
        
        # Build ISA RO-Crate
        print("Building ISA RO-Crate...")
        builder = ISAROCrateBuilder()
        crate = builder.build_from_parsed_data(parsed_data)
        
        if args.json:
            # Output as JSON-LD
            print("\nRO-Crate JSON-LD:")
            print(json.dumps(builder.to_json(), indent=2))
        else:
            # Write to disk
            output_path = Path(args.output)
            builder.save(str(output_path))
            print(f"✓ RO-Crate written to: {output_path}")
            print(f"  - Metadata: {output_path / 'ro-crate-metadata.json'}")
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()