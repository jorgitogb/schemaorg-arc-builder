"""
Submit ARC to GitLab.

Usage:
    python gitlab_submit.py <arc_directory> [--name PROJECT_NAME] [--description DESCRIPTION] [--overwrite]

Example:
    python gitlab_submit.py output_crates/edal_arc/arc --name my-arc-project --overwrite
"""

import argparse
from pathlib import Path
from gitlab_submitter import GitLabSubmitter


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
    
    args = parser.parse_args()
    
    try:
        # Initialize GitLab submitter
        submitter = GitLabSubmitter(config_path=args.env)
        
        if args.clear_group:
            print("Clearing GitLab group...")
            result = submitter.clear_group(dry_run=args.dry_run)
            print(f"\nDone: {result['deleted']}/{result['total']} projects deleted")
            return 0
        
        # If no name provided, extract Investigation Identifier from isa.investigation.xlsx
        project_name = args.name
        if not project_name:
            investigation_file = args.arc_directory / 'isa.investigation.xlsx'
            if investigation_file.exists():
                try:
                    import openpyxl
                    wb = openpyxl.load_workbook(investigation_file)
                    ws = wb['isa_investigation']
                    # Investigation Identifier is in cell B7
                    identifier = ws['B7'].value
                    if identifier:
                        project_name = identifier
                        print(f"Using Investigation Identifier as project name: {project_name}")
                except Exception as e:
                    print(f"Warning: Could not read Investigation Identifier: {e}")
        
        # Submit ARC
        project = submitter.submit_arc(
            arc_directory=args.arc_directory,
            project_name=args.name,
            description=args.description,
            overwrite=args.overwrite,
            branch=args.branch
        )
        
        print("\n✓ Success! ARC is now available at:")
        print(f"  {project['web_url']}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
