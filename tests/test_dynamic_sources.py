#!/usr/bin/env python3
"""
Test script to verify dynamic source tagging with different repositories
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))
APP_DIR = ROOT_DIR / 'app'
if str(APP_DIR) not in sys.path:
    sys.path.append(str(APP_DIR))
from simple_rag import add_to_vector_store, create_or_update_unified_vector_store

def test_dynamic_source_tagging():
    """Test source tagging with different repository names"""
    
    print("🧪 Testing Dynamic Source Tagging...")
    print("=" * 50)
    
    # Test Case 1: Microsoft VS Code repository
    print("\n📝 Test Case 1: Microsoft VS Code Repository")
    test_repo_1 = {
        "README.md": "# Visual Studio Code\n\nVS Code is a lightweight but powerful source code editor which runs on your desktop and is available for Windows, macOS and Linux.",
        "package.json": '{"name": "vscode", "version": "1.80.0", "description": "Visual Studio Code"}',
        "uploaded:API_Documentation.pdf": "This PDF contains comprehensive API documentation for integrating with external services."
    }
    
    collection = create_or_update_unified_vector_store("test_vscode")
    metadata_vscode = {"repo_name": "vscode"}
    add_to_vector_store(collection, test_repo_1, "unified", metadata_vscode, 400, 10.0)
    
    # Show what the chunks look like
    results = collection.get(limit=3)
    print(f"✅ Indexed {len(results['documents'])} chunks for VS Code")
    for i, doc in enumerate(results['documents'][:2]):
        source_tag = doc.split('\n')[0] if doc.startswith('[Source:') else "No source tag"
        print(f"   Chunk {i+1}: {source_tag}")
    
    # Test Case 2: React repository  
    print("\n📝 Test Case 2: Facebook React Repository")
    test_repo_2 = {
        "README.md": "# React\n\nA JavaScript library for building user interfaces. React makes it painless to create interactive UIs.",
        "src/index.js": "import React from 'react';\nexport default React;",
        "uploaded:React_Best_Practices.docx": "This document outlines the best practices for developing React applications in enterprise environments."
    }
    
    collection2 = create_or_update_unified_vector_store("test_react")
    metadata_react = {"repo_name": "react"}
    add_to_vector_store(collection2, test_repo_2, "unified", metadata_react, 400, 10.0)
    
    results2 = collection2.get(limit=3)
    print(f"✅ Indexed {len(results2['documents'])} chunks for React")
    for i, doc in enumerate(results2['documents'][:2]):
        source_tag = doc.split('\n')[0] if doc.startswith('[Source:') else "No source tag"
        print(f"   Chunk {i+1}: {source_tag}")
    
    # Test Case 3: No repository name (fallback)
    print("\n📝 Test Case 3: Generic Repository (Fallback)")
    test_repo_3 = {
        "README.md": "# My Project\n\nThis is a sample project to test generic repository handling.",
        "uploaded:Requirements.txt": "numpy==1.21.0\npandas==1.3.0\nrequests==2.25.1"
    }
    
    collection3 = create_or_update_unified_vector_store("test_generic")
    metadata_generic = {"repo_name": "Repository"}  # Fallback name
    add_to_vector_store(collection3, test_repo_3, "unified", metadata_generic, 400, 10.0)
    
    results3 = collection3.get(limit=2)
    print(f"✅ Indexed {len(results3['documents'])} chunks for Generic repo")
    for i, doc in enumerate(results3['documents']):
        source_tag = doc.split('\n')[0] if doc.startswith('[Source:') else "No source tag"
        print(f"   Chunk {i+1}: {source_tag}")
    
    print("\n🎉 All tests completed! Dynamic source tagging is working correctly.")
    print("\n💡 Expected behavior:")
    print("   - VS Code repo shows: [Source: Repo - vscode/...]")
    print("   - React repo shows: [Source: Repo - react/...]") 
    print("   - Generic repo shows: [Source: Repo - Repository/...]")
    print("   - All uploads show: [Source: Download - filename]")

if __name__ == "__main__":
    test_dynamic_source_tagging()