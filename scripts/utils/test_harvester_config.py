#!/usr/bin/env python3
"""
Test script to verify GitHub harvester configuration.
"""

import os
from scripts.github_harvester import GitHubHarvester

def test_configuration():
    """Test that configuration is properly loaded."""
    print("Testing GitHub harvester configuration...")
    
    # Create harvester instance
    harvester = GitHubHarvester()
    
    # Check if required environment variables are set
    if not harvester.token:
        print("❌ GITHUB_TOKEN not set in environment")
        return False
        
    if not harvester.repo:
        print("❌ GITHUB_REPOSITORY not set in environment")
        return False
    
    print(f"✅ GitHub token configured (first 10 chars: {harvester.token[:10]}...)")
    print(f"✅ Repository: {harvester.repo}")
    print(f"✅ Branch: {harvester.branch}")
    print(f"✅ Metadata path: {harvester.metadata_path}")
    
    # Validate token (this would require actual API call)
    # For now just check if it's formatted correctly
    if harvester.token.startswith('ghp_') or harvester.token.startswith('github_pat_'):
        print("✅ Token format looks valid")
        return True
    else:
        print("⚠️ Token format may not be valid")
        return True  # Still return True since we're just testing config

if __name__ == "__main__":
    test_configuration()