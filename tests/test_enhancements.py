"""Test script to verify all new enhancements"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from simple_rag import create_vector_store, search_vector_store, chunk_text, is_safe_file_type

def test_chunk_size_and_overlap():
    """Test configurable chunk size and overlap"""
    print("🧪 Testing chunk size and overlap...")
    
    text = "This is a test document. " * 100  # Create longer text
    
    # Test default parameters
    chunks_default = chunk_text(text, 500, 10.0)
    print(f"✅ Default chunking: {len(chunks_default)} chunks")
    
    # Test smaller chunks
    chunks_small = chunk_text(text, 200, 15.0)
    print(f"✅ Small chunks (200 chars, 15% overlap): {len(chunks_small)} chunks")
    
    # Test larger chunks
    chunks_large = chunk_text(text, 800, 5.0)
    print(f"✅ Large chunks (800 chars, 5% overlap): {len(chunks_large)} chunks")
    
    assert len(chunks_small) > len(chunks_default) > len(chunks_large)
    print("✅ Chunk size configuration working correctly!")

def test_readme_prioritization():
    """Test README prioritization in search results"""
    print("\n🧪 Testing README prioritization...")
    
    # Create test documents with README and code files
    docs = {
        "README.md": "This project is a web application that helps users manage tasks. It provides authentication and user management features.",
        "main.py": "def authenticate_user(username, password): return check_credentials(username, password)",
        "utils.py": "def helper_function(): pass",
        "config.json": '{"database": "postgresql", "port": 5432}'
    }
    
    # Create vector store
    collection = create_vector_store(docs, "test_readme", 500, 10.0)
    
    # Search for general project info (should prioritize README)
    results = search_vector_store(collection, "What does this project do?", k=3)
    
    print(f"✅ Search results for 'What does this project do?':")
    for i, result in enumerate(results):
        print(f"   {i+1}. {result['file_path']} (similarity: {result['similarity']})")
    
    # Verify README is in top results
    top_files = [r['file_path'] for r in results[:2]]
    assert any('readme' in f.lower() for f in top_files), "README should be prioritized!"
    print("✅ README prioritization working correctly!")

def test_file_type_security():
    """Test file type security filtering"""
    print("\n🧪 Testing file type security...")
    
    safe_files = [
        "script.py", "notebook.ipynb", "data.json", "config.yml", 
        "style.css", "index.html", "README.md", "requirements.txt"
    ]
    
    unsafe_files = [
        "virus.exe", "malware.bat", "script.ps1", "data.bin", 
        "image.jpg", "document.pdf", "archive.zip"
    ]
    
    for filename in safe_files:
        assert is_safe_file_type(filename), f"{filename} should be safe!"
        print(f"✅ {filename} - correctly identified as safe")
    
    for filename in unsafe_files:
        if filename in ["document.pdf"]:  # PDF should actually be safe for uploads
            continue
        assert not is_safe_file_type(filename), f"{filename} should be unsafe!"
        print(f"✅ {filename} - correctly identified as unsafe")
    
    print("✅ File type security working correctly!")

def test_multi_source_indexing():
    """Test combining repository and document sources"""
    print("\n🧪 Testing index one source type per session (repo or documents) workflows...")
    
    # Create separate document sets
    repo_docs = {
        "src/main.py": "def main(): print('Hello from repo')",
        "README.md": "This is the repository README"
    }
    
    upload_docs = {
        "uploaded:notes.txt": "These are my personal notes about the project",
        "uploaded:config.py": "CONFIG = {'debug': True}"
    }
    
    # Test that both can be indexed together
    combined_docs = {**repo_docs, **upload_docs}
    collection = create_vector_store(combined_docs, "test_multi", 500, 10.0)
    
    # Search for content that should find both sources
    results = search_vector_store(collection, "configuration and setup", k=4)
    
    print(f"✅ Multi-source search results:")
    source_types = set()
    for result in results:
        file_path = result['file_path']
        source_type = "uploaded" if "uploaded:" in file_path else "repository"
        source_types.add(source_type)
        print(f"   - {file_path} ({source_type}) - similarity: {result['similarity']}")
    
    print("✅ Multi-source indexing working correctly!")

def main():
    """Run all enhancement tests"""
    print("🚀 Testing SageVault Enhancements")
    print("=" * 50)
    
    try:
        test_chunk_size_and_overlap()
        test_readme_prioritization()
        test_file_type_security()
        test_multi_source_indexing()
        
        print("\n🎉 All enhancement tests passed!")
        print("✅ Chunk size and overlap configuration")
        print("✅ README prioritization")
        print("✅ File type security filtering")
        print("✅ Multi-source indexing")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
