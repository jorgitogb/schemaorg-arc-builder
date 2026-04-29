#!/usr/bin/env python3
"""
Harvest metadata from GitHub and process through the full pipeline.
"""

import os
import sys
import json
from pathlib import Path
from schemaorg_arc_builder import SchemaOrgParser, ISAROCrateBuilder
from scripts.harvest.github_harvester import GitHubHarvester
from scripts.process.arc_creator import ARCCreator
from scripts.submit.gitlab_submitter import GitLabSubmitter

def main():
    """Main harvesting and processing workflow."""
    try:
        # Initialize components
        harvester = GitHubHarvester()
        parser = SchemaOrgParser()
        builder = ISAROCrateBuilder()
        gitlab_submitter = GitLabSubmitter()

        # Harvest metadata from GitHub
        print("🔍 Harvesting metadata from GitHub...")
        metadata_files = harvester.harvest_all_metadata()

        if not metadata_files:
            print("⚠️ No metadata files found")
            return

        print(f"📊 Found {len(metadata_files)} metadata files")

        # Process each file
        for i, metadata in enumerate(metadata_files, 1):
            if metadata['status'] != 'success':
                print(f"❌ Failed to process {metadata['filename']}: {metadata['error']}")
                continue

            print(f"🔧 [{i}/{len(metadata_files)}] Processing {metadata['filename']}...")

            try:
                # Parse JSON-LD content
                parsed_data = parser.parse(metadata['content'])

                # Build RO-Crate (in memory)
                crate = builder.build_from_parsed_data(parsed_data)

                # Generate ARC name
                arc_name = f"arc-{Path(metadata['filename']).stem}"

                # Create ARC structure
                arc_creator = ARCCreator()
                arc = arc_creator.create_arc_from_dict(crate.get_metadata_dict())

                # Write ARC to data/output directory
                output_dir = Path("data/output")
                output_dir.mkdir(exist_ok=True)
                arc_path = output_dir / arc_name
                arc_path.mkdir(exist_ok=True)
                arc_creator.write_arc(arc, arc_name)

                # Push to GitLab
                print(f"🚀 Pushing {arc_name} to GitLab...")
                project = gitlab_submitter.submit_arc(
                    arc_directory=arc_path,
                    project_name=arc_name,
                    description=f"ARC generated from {metadata['filename']}"
                )

                print(f"✅ Successfully pushed: {project['web_url']}")

                # Clean up temporary directory
                # (Note: ArcCreator.write_arc already writes to the output_dir, so nothing to clean)

            except Exception as e:
                print(f"❌ Error processing {metadata['filename']}: {e}")

        print("🎉 Harvesting and processing complete!")

    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()