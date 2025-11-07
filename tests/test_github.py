"""Test script for GitHub integration module."""

import os
import sys
import json
from datetime import datetime

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.github import GitHubClient
from src.utils.error_handling import FSRException

def test_logger(level: str, message: str):
    """Simple test logger function."""
    print(f"[{level}] {message}")

def progress_callback(current: int, total: int, done: bool, message: str):
    """Progress callback for downloads."""
    if not done:
        progress = (current / total) * 100 if total > 0 else 0
        print(f"\r{message} {progress:.1f}%", end="")
    else:
        print(f"\n{message}")

def main():
    """Run tests for GitHub integration."""
    client = GitHubClient(logger=test_logger)
    
    print("\n1. Testing release fetching...")
    try:
        releases = client.get_releases()
        if not releases:
            print("No releases found")
            return
            
        print(f"Found {len(releases)} releases")
        for i, release in enumerate(releases[:3], 1):
            print(f"Release {i}:")
            print(f"  Tag: {release.get('tag_name', 'N/A')}")
            print(f"  Published: {release.get('published_at', 'N/A')}")
            print(f"  Title: {release.get('name', 'N/A')}")
    except FSRException as e:
        print(f"Error fetching releases: {e}")
        return
        
    print("\n2. Testing latest release...")
    try:
        latest = client.get_latest_release()
        if not latest:
            print("Could not get latest release")
            return
            
        print(f"Latest release details:")
        print(f"  Tag: {latest.get('tag_name', 'N/A')}")
        print(f"  Published: {latest.get('published_at', 'N/A')}")
        print(f"  Title: {latest.get('name', 'N/A')}")
        print(f"  Assets: {len(latest.get('assets', []))}")
    except FSRException as e:
        print(f"Error getting latest release: {e}")
        return
        
    print("\n3. Testing update check...")
    try:
        current_version = "1.0.0"  # Test version
        has_update, new_version = client.check_for_updates(current_version)
        if has_update:
            print(f"Update available: {new_version}")
            print(f"Current version: {current_version}")
        else:
            print(f"No update available (current version: {current_version})")
    except FSRException as e:
        print(f"Error checking updates: {e}")
        
    if latest:  # Only proceed if we have a latest release
        print("\n4. Testing release notes...")
        try:
            notes = client.get_release_notes()
            if notes and notes != "No release notes available.":
                print("Latest release notes:")
                print("-------------------")
                if len(notes) > 200:
                    print(notes[:200].rstrip() + "...")
                else:
                    print(notes)
                print("-------------------")
            else:
                print("No release notes available")
        except FSRException as e:
            print(f"Error getting release notes: {e}")
            
        print("\n5. Testing release download...")
        try:
            success = client.download_release(latest, progress_callback)
            if success:
                print("Download and extraction successful!")
            else:
                print("Download or extraction failed!")
        except FSRException as e:
            print(f"Error downloading release: {e}")

if __name__ == "__main__":
    main()