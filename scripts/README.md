# Scripts

This directory contains utility scripts for the schemaorg-arc-builder project.

## Directory Structure

- **harvest/** - GitHub harvesting scripts
- **process/** - Processing and ARC creation scripts  
- **submit/** - GitLab submission scripts
- **utils/** - Utility scripts and helpers

## Available Scripts

### Harvest Scripts
- **github_harvester.py** - Harvests metadata files from private GitHub repositories

### Process Scripts  
- **arc_creator.py** - Creates ARC structures from ISA RO-Crate metadata using ARCtrl

### Submit Scripts
- **gitlab_submitter.py** - Submits ARC directories to GitLab repositories using the GitLab API
- **gitlab_submit.py** - Command-line interface for GitLab submission

### Utility Scripts
- **test_harvester_config.py** - Test script to verify GitHub harvester configuration

## Usage

### Testing Configuration
```bash
python scripts/utils/test_harvester_config.py
```

### Harvesting and Processing
```bash
# First set your environment variables
export GITHUB_TOKEN=your_token_here
export GITHUB_REPOSITORY=owner/repo
export GITHUB_BRANCH=main
export GITHUB_METADATA_PATH=metadata

# Then run the harvest and process workflow
python scripts/harvest/harvest_and_process.py
```

## Environment Variables

See `.env.example` for configuration details.