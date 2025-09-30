#!/usr/bin/env python3
"""
Test GitHub URL parsing functionality
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))
# Import the GitHub URL parsing function from streamlit app
def parse_github_url(url):
    """Extract repository name from GitHub URL"""
    import re
    if not url:
        return "Repository"
    
    # Handle different GitHub URL formats
    patterns = [
        r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$',
        r'github\.com[:/]([^/]+/[^/]+?)/.*$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url.rstrip('/'))
        if match:
            repo_path = match.group(1)
            # Extract just the repository name (not owner/repo)
            return repo_path.split('/')[-1]
    
    return "Repository"

def test_github_url_parsing():
    """Test GitHub URL parsing with various formats"""
    
    print("🔗 Testing GitHub URL Parsing...")
    print("=" * 50)
    
    test_urls = [
        "https://github.com/microsoft/vscode",
        "https://github.com/facebook/react.git", 
        "git@github.com:nodejs/node.git",
        "https://github.com/mwill20/SageVault/tree/main",
        "https://github.com/tensorflow/tensorflow/blob/master/README.md",
        "https://github.com/python/cpython",
        "",  # Empty URL
        "invalid-url",  # Invalid URL
    ]
    
    for url in test_urls:
        repo_name = parse_github_url(url)
        print(f"URL: {url or '(empty)'}")
        print(f"Extracted repo name: '{repo_name}'")
        print(f"Source tag would be: [Source: Repo - {repo_name}/filename]")
        print("-" * 30)

if __name__ == "__main__":
    test_github_url_parsing()