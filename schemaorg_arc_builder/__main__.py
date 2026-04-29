"""Schema.org to ISA RO-Crate Parser - Main Entry Point."""

import argparse
import json
import logging
import sys
from pathlib import Path

from schemaorg_arc_builder import ISAROCrateBuilder, SchemaOrgParser

logger = logging.getLogger(__name__)


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
    parser.add_argument(
        "--harvest",
        action="store_true",
        help="Harvest metadata from GitHub repository"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug output"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress normal output"
    )

    args = parser.parse_args()

    if args.quiet:
        level = logging.WARNING
    elif args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    # Handle harvesting workflow if requested
    if args.harvest:
        try:
            logger.info("Starting GitHub harvest workflow...")
            # Import here to avoid circular dependencies
            from scripts.github_harvester import GitHubHarvester
            harvester = GitHubHarvester()
            
            # For demonstration, let's process the input file normally
            # and then show how harvesting would work
            input_path = Path(args.input)
            if not input_path.exists():
                logger.error(f"Input file '{args.input}' not found")
                sys.exit(1)
                
            logger.info("Harvest workflow would fetch metadata from GitHub repository")
            logger.info("This would process all files from the configured repository")
            
        except Exception as e:
            logger.error(f"Harvesting failed: {e}")
            sys.exit(1)
        return
    
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file '{args.input}' not found")
        sys.exit(1)

    try:
        logger.info(f"Parsing Schema.org metadata from: {args.input}")
        schemaorg_parser = SchemaOrgParser()
        parsed_data = schemaorg_parser.parse_file(input_path)

        datasets = parsed_data.get('datasets', [])
        num_datasets = len(datasets)

        if num_datasets == 0:
            logger.error("No datasets found in input file")
            sys.exit(1)

        # Prepare shared entities (persons, orgs, grants, publications)
        shared_entities = {
            'persons': parsed_data.get('persons', []),
            'organizations': parsed_data.get('organizations', []),
            'grants': parsed_data.get('grants', []),
            'publications': parsed_data.get('publications', [])
        }

        output_base = Path(args.output)
        builder = ISAROCrateBuilder()

        if num_datasets == 1:
            # Single dataset - original behavior
            logger.info("Building ISA RO-Crate for single dataset...")
            crate = builder.build_single_dataset(datasets[0], shared_entities)

            if args.json:
                print(json.dumps(builder.to_json(), indent=2))
            else:
                builder.save(str(output_base))
                logger.info(f"RO-Crate written to: {output_base}")
                logger.info(f"  Metadata: {output_base / 'ro-crate-metadata.json'}")
        else:
            # Multiple datasets - create subdirectory per dataset
            logger.info(f"Building {num_datasets} ARCs from {num_datasets} datasets...")

            for i, dataset in enumerate(datasets):
                # Generate deterministic names
                dir_name, gitlab_name = builder.generate_arc_name(args.input, dataset)
                dataset_output = output_base / dir_name

                logger.info(f"[{i+1}/{num_datasets}] Building ARC: {dir_name}")

                # Build ARC for this dataset
                crate = builder.build_single_dataset(dataset, shared_entities)

                if args.json:
                    print(f"\n--- Dataset {i+1}: {dir_name} ---")
                    print(json.dumps(builder.to_json(), indent=2))
                else:
                    builder.save(str(dataset_output))
                    logger.info(f"  ARC directory: {dataset_output}")
                    logger.info(f"  GitLab project (suggested): {gitlab_name}")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"{e}")
        sys.exit(2)
    except Exception as e:
        logger.error(f"{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()