# Scripts

This directory contains executable scripts for working with ARCs and GitLab.

## Files

- **arc_creator.py**: Create ARC structures from RO-Crate metadata using ARCtrl
- **gitlab_submit.py**: CLI tool for submitting ARCs to GitLab
- **gitlab_submitter.py**: GitLab API client for ARC submission

## Usage

### Create an ARC
```bash
uv run python scripts/arc_creator.py output_crates/example/ro-crate-metadata.json
```

### Submit to GitLab
```bash
uv run python scripts/gitlab_submit.py output_crates/example/arc --branch main
```
