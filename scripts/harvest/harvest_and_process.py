#!/usr/bin/env python3
"""
Main script to harvest metadata from GitHub and process through the full pipeline.
"""
import argparse
import logging
import os
import sys
from pathlib import Path

from harvest.github_harvester import GitHubHarvester
from process.arc_creator import ARCCreator
from submit.gitlab_submitter import GitLabSubmitter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description="Harvest metadata from GitHub and process through full pipeline"
    )
    
    parser.add_argument(
        '--harvest-only',
        action='store_true',
        help='Only harvest metadata, do not process or submit'
    )
    
    parser.add_argument(
        '--process-only',
        action='store_true',
        help='Only process harvested metadata, do not harvest or submit'
    )
    
    parser.add_argument(
        '--submit-only',
        action='store_true',
        help='Only submit processed ARCs, do not harvest or process'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Do not actually submit to GitLab (only for --submit-only or full pipeline)'
    )

    parser.add_argument(
        '--env',
        type=str,
        help='Path to .env file (defaults to .env in current directory)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of datasets to process (default: no limit)'
    )

    args = parser.parse_args()
    
    # Check for mutually exclusive arguments
    if sum([args.harvest_only, args.process_only, args.submit_only]) > 1:
        logger.error("Only one of --harvest-only, --process-only, or --submit-only can be specified")
        sys.exit(1)
    
    # Determine what to do based on arguments
    if args.harvest_only:
        logger.info("Starting harvest-only mode...")
        harvester = GitHubHarvester()
        harvested = harvester.harvest_all_metadata()
        
        # Apply limit if specified
        if args.limit:
            harvested = harvested[:args.limit]
            logger.info(f"Applied limit: processing first {args.limit} of {len(harvested)} metadata files")
        
        logger.info(f"Harvested {len(harvested)} metadata files")
        
        # Save harvested files
        data_dir = Path("data/harvested")
        data_dir.mkdir(exist_ok=True)
        
        for i, metadata in enumerate(harvested):
            save_path = data_dir / f"harvested_{i:03d}.json"
            save_path.write_text(metadata['content'])
            logger.info(f"Saved {save_path}")
            
        logger.info("Harvest completed successfully")
        
    elif args.process_only:
        logger.info("Starting process-only mode...")
        # Process existing harvested files
        data_dir = Path("data/harvested")
        if not data_dir.exists():
            logger.error("No harvested data found. Run harvest first.")
            sys.exit(1)
            
        processed_dir = Path("data/processed")
        processed_dir.mkdir(exist_ok=True)
        
        # Process each harvested file
        harvested_files = sorted(data_dir.glob("*.json"))
        
        # Apply limit if specified
        if args.limit:
            harvested_files = harvested_files[:args.limit]
            logger.info(f"Applied limit: processing first {args.limit} of {len(harvested_files)} harvested files")
        
        for harvested_file in harvested_files:
            logger.info(f"Processing {harvested_file.name}...")
            
            # Create ARCCreator with the harvested file
            arc_creator = ARCCreator()
            arc_dir = arc_creator.create_arc_from_json_file(
                harvested_file,
                output_dir=processed_dir / harvested_file.stem
            )
            logger.info(f"Created ARC at {arc_dir}")
            
        logger.info("Processing completed successfully")
        
    elif args.submit_only:
        logger.info("Starting submit-only mode...")
        if args.dry_run:
            logger.info("Dry run mode - no actual submissions will be made")
        
        # Submit existing processed ARCs
        processed_dir = Path("data/processed")
        if not processed_dir.exists():
            logger.error("No processed data found. Run process first.")
            sys.exit(1)
            
        submitter = GitLabSubmitter(config_path=args.env)
        
        arc_dirs = sorted(processed_dir.glob("*"))
        
        # Apply limit if specified
        if args.limit:
            arc_dirs = arc_dirs[:args.limit]
            logger.info(f"Applied limit: submitting first {args.limit} of {len(arc_dirs)} ARCs")
        
        for arc_dir in arc_dirs:
            if arc_dir.is_dir():
                try:
                    if args.dry_run:
                        logger.info(f"[DRY RUN] Would submit {arc_dir.name}")
                        # Just show what would happen
                    else:
                        logger.info(f"Submitting {arc_dir.name}...")
                        project = submitter.submit_arc(
                            arc_directory=arc_dir,
                            project_name=arc_dir.name
                        )
                        logger.info(f"Submitted to: {project['web_url']}")
                except Exception as e:
                    logger.error(f"Failed to submit {arc_dir.name}: {e}")
        
        logger.info("Submission completed successfully")
        
    else:
        # Full pipeline: harvest -> process -> submit
        logger.info("Starting full pipeline...")
        
        # Step 1: Harvest
        logger.info("Step 1: Harvesting metadata from GitHub...")
        harvester = GitHubHarvester()
        harvested = harvester.harvest_all_metadata()
        
        # Apply limit if specified
        if args.limit:
            harvested = harvested[:args.limit]
            logger.info(f"Applied limit: processing first {args.limit} of {len(harvested)} metadata files")
        
        logger.info(f"Harvested {len(harvested)} metadata files")
        
        # Save harvested files
        data_dir = Path("data/harvested")
        data_dir.mkdir(exist_ok=True)
        
        for i, metadata in enumerate(harvested):
            save_path = data_dir / f"harvested_{i:03d}.json"
            save_path.write_text(metadata['content'])
            logger.info(f"Saved {save_path}")
            
        # Step 2: Process
        logger.info("Step 2: Processing harvested metadata...")
        processed_dir = Path("data/processed")
        processed_dir.mkdir(exist_ok=True)
        
        # Process each harvested file
        harvested_files = sorted(data_dir.glob("*.json"))
        
        # Apply limit if specified
        if args.limit:
            harvested_files = harvested_files[:args.limit]
            logger.info(f"Applied limit: processing first {args.limit} of {len(harvested_files)} harvested files")
        
        for harvested_file in harvested_files:
            logger.info(f"Processing {harvested_file.name}...")
            
            # Create ARCCreator with the harvested file
            arc_creator = ARCCreator()
            arc_dir = arc_creator.create_arc_from_json_file(
                harvested_file,
                output_dir=processed_dir / harvested_file.stem
            )
            logger.info(f"Created ARC at {arc_dir}")
            
        # Step 3: Submit
        logger.info("Step 3: Submitting ARCs to GitLab...")
        if args.dry_run:
            logger.info("Dry run mode - no actual submissions will be made")
        
        submitter = GitLabSubmitter(config_path=args.env)
        
        arc_dirs = sorted(processed_dir.glob("*"))
        
        # Apply limit if specified
        if args.limit:
            arc_dirs = arc_dirs[:args.limit]
            logger.info(f"Applied limit: submitting first {args.limit} of {len(arc_dirs)} ARCs")
        
        for arc_dir in arc_dirs:
            if arc_dir.is_dir():
                try:
                    if args.dry_run:
                        logger.info(f"[DRY RUN] Would submit {arc_dir.name}")
                    else:
                        logger.info(f"Submitting {arc_dir.name}...")
                        project = submitter.submit_arc(
                            arc_directory=arc_dir,
                            project_name=arc_dir.name
                        )
                        logger.info(f"Submitted to: {project['web_url']}")
                except Exception as e:
                    logger.error(f"Failed to submit {arc_dir.name}: {e}")
        
        logger.info("Full pipeline completed successfully")

if __name__ == "__main__":
    main()