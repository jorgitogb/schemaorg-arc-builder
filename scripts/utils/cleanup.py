#!/usr/bin/env python3
"""
Cleanup script to remove old temporary files and directories.
"""

import os
import shutil
from pathlib import Path

def cleanup_temp_files():
    """Remove temporary files and directories."""
    print("🧹 Cleaning up temporary files...")
    
    # Remove temporary directories
    temp_dirs = [
        'temp_arc_*',
        'test_output_*',
        'data/temp*'
    ]
    
    for pattern in temp_dirs:
        for path in Path('.').glob(pattern):
            if path.is_dir():
                print(f"  Removing directory: {path}")
                shutil.rmtree(path)
            elif path.is_file():
                print(f"  Removing file: {path}")
                path.unlink()
    
    # Remove data directories that might be empty
    data_dirs = ['data/harvested', 'data/processed', 'data/output']
    for data_dir in data_dirs:
        path = Path(data_dir)
        if path.exists():
            # Only remove if directory is empty or has .gitkeep
            contents = list(path.iterdir())
            if not contents or (len(contents) == 1 and contents[0].name == '.gitkeep'):
                print(f"  Skipping empty directory: {data_dir}")
            else:
                print(f"  Keeping populated directory: {data_dir}")
    
    print("✅ Cleanup completed!")

if __name__ == "__main__":
    cleanup_temp_files()