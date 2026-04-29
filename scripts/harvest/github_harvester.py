"""
GitHub harvester for fetching metadata from private repositories.
"""

import os
import requests
import base64
import json
from typing import List, Dict, Optional
from pathlib import Path

class GitHubHarvester:
    """Harvest metadata files from private GitHub repositories."""

    def __init__(self):
        """Initialize with environment variables."""
        self.token = os.getenv('GITHUB_TOKEN')
        self.repo = os.getenv('GITHUB_REPOSITORY', 'fairagro/middleware_repo')
        self.branch = os.getenv('GITHUB_BRANCH', 'main')
        self.metadata_path = os.getenv('GITHUB_METADATA_PATH', '')
        self.api_url = f"https://api.github.com/repos/{self.repo}"
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }

    def validate_token(self) -> bool:
        """Validate GitHub token and repository access."""
        try:
            response = requests.get(
                f"{self.api_url}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Token validation failed: {e}")
            return False

    def list_metadata_files(self) -> List[str]:
        """List all JSON-LD files in the metadata directory."""
        url = f"{self.api_url}/contents/{self.metadata_path}?ref={self.branch}"
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()

        files = []
        for item in response.json():
            if item['type'] == 'file' and item['name'].endswith('.json'):
                files.append(item['name'])
        return files

    def download_metadata_file(self, filename: str) -> str:
        """Download and decode a metadata file."""
        file_path = f"{self.metadata_path}/{filename}" if self.metadata_path else filename
        url = f"{self.api_url}/contents/{file_path}?ref={self.branch}"
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()

        content = response.json()['content']
        return base64.b64decode(content).decode('utf-8')

    def harvest_all_metadata(self) -> List[Dict]:
        """Harvest all metadata files from the repository."""
        if not self.validate_token():
            raise Exception("GitHub token validation failed")

        files = self.list_metadata_files()
        results = []

        for filename in files:
            try:
                content = self.download_metadata_file(filename)
                results.append({
                    'filename': filename,
                    'content': content,
                    'status': 'success'
                })
            except Exception as e:
                results.append({
                    'filename': filename,
                    'error': str(e),
                    'status': 'failed'
                })

        return results

    def harvest_single_file(self, filename: str) -> Optional[str]:
        """Harvest a single metadata file."""
        try:
            return self.download_metadata_file(filename)
        except Exception as e:
            print(f"Failed to harvest {filename}: {e}")
            return None