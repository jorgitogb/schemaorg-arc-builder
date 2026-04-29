"""
Submit ARC to GitLab.

Usage:
    python gitlab_submit.py <arc_directory> [--name PROJECT_NAME] [--description DESCRIPTION] [--overwrite]

Example:
    python gitlab_submit.py output_crates/edal_arc/arc --name my-arc-project --overwrite
"""

import argparse
import logging
from pathlib import Path

from gitlab_submitter import GitLabSubmitter

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Submit ARC directory to GitLab',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Configuration:
    Create a .env file with:
        GITLAB_URL=https://your-gitlab-instance.com
        GITLAB_PRIVATE_TOKEN=your-private-token
        GITLAB_NAMESPACE_ID=your-namespace-id
        GITLAB_GROUP_ID=your-group-id
        """
    )
    
    parser.add_argument(
        'arc_directory',
        type=Path,
        nargs='?',  # Make optional
        help='Path to ARC directory to submit'
    )
    
    parser.add_argument(
        '--name',
        type=str,
        help='GitLab project name (defaults to directory name)'
    )
    
    parser.add_argument(
        '--description',
        type=str,
        default='',
        help='Project description'
    )
    
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Delete and recreate project if it already exists'
    )
    
    parser.add_argument(
        '--branch',
        type=str,
        default='main',
        help='Branch name to commit to (default: main)'
    )
    
    parser.add_argument(
        '--env',
        type=str,
        help='Path to .env file (defaults to .env in current directory)'
    )
    
    parser.add_argument(
        '--clear-group',
        action='store_true',
        help='Delete all projects in the configured GitLab group'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting (use with --clear-group)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable debug output'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress normal output'
    )

    args = parser.parse_args()

    if args.quiet:
        level = logging.WARNING
    elif args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")
    
    try:
        # Initialize GitLab submitter
        submitter = GitLabSubmitter(config_path=args.env)
        
        if args.clear_group:
            logger.info("Clearing GitLab group...")
            result = submitter.clear_group(dry_run=args.dry_run)
            logger.info(f"Done: {result['deleted']}/{result['total']} projects deleted")
            return 0

        arc_path = Path(args.arc_directory)

        # Check if this is a single ARC or a directory of ARCs
        # Accept either full ARC (isa.investigation.xlsx) or RO-Crate (ro-crate-metadata.json)
        is_single_arc = arc_path.is_file() or (arc_path / 'isa.investigation.xlsx').exists() or (arc_path / 'ro-crate-metadata.json').exists()

        if is_single_arc:
            # Single ARC submission
            project_name = args.name
            if not project_name:
                project_name = arc_path.name

            logger.info(f"Submitting ARC: {project_name}")
            project = submitter.submit_or_update_arc(
                arc_directory=arc_path,
                project_name=project_name,
                description=args.description,
                overwrite=args.overwrite
            )
            logger.info(f"Success! ARC is now available at: {project['web_url']}")
        else:
            # Directory with multiple ARCs - pipeline mode
            logger.info(f"Pipeline mode: Processing all ARCs in {arc_path}")

            arc_dirs = []
            for subdir in sorted(arc_path.iterdir()):
                if subdir.is_dir() and ((subdir / 'isa.investigation.xlsx').exists() or (subdir / 'ro-crate-metadata.json').exists()):
                    arc_dirs.append(subdir)

            if not arc_dirs:
                logger.warning(f"No ARCs found in {arc_path}")
                return 0

            logger.info(f"Found {len(arc_dirs)} ARC(s)")

            results = {'created': 0, 'updated': 0, 'skipped': 0}
            for i, subdir in enumerate(arc_dirs, 1):
                logger.info(f"[{i}/{len(arc_dirs)}] Processing: {subdir.name}")

                # Check if project exists before calling submit_or_update
                existing = submitter.project_exists(subdir.name)

                if existing and not args.overwrite:
                    # Check if changed
                    rocrate_file = subdir / 'ro-crate-metadata.json'
                    if rocrate_file.exists() and submitter._has_file_changed(existing['id'], rocrate_file):
                        logger.info("  Detected changes, updating...")
                        submitter.submit_or_update_arc(subdir, subdir.name, f"ARC: {subdir.name}", args.overwrite)
                        results['updated'] += 1
                    else:
                        logger.info("  No changes detected, skipping...")
                        results['skipped'] += 1
                else:
                    submitter.submit_or_update_arc(subdir, subdir.name, f"ARC: {subdir.name}", args.overwrite)
                    if existing:
                        results['updated'] += 1
                    else:
                        results['created'] += 1

            logger.info(f"Done! Created: {results['created']}, Updated: {results['updated']}, Skipped: {results['skipped']}")

    except Exception as e:
        logger.error(f"{e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
