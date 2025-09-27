#!/usr/bin/env python3
"""Minimal test to verify the core RAG functionality works"""

print("Testing ChromaDB and RAG functionality...")

try:
    # Test 1: Basic imports
    print("1. Testing imports...")
    from app.rag_utils import build_store, retrieve
    print("   ✅ Imports successful")
    
    # Test 2: Create a simple collection
    print("2. Testing collection creation...")
    test_corpus = {
        "README.md": "# Test Project\nThis is a test project for SageVault.",
        "main.py": "def hello():\n    print('Hello World')\n\nif __name__ == '__main__':\n    hello()"
    }
    collection = build_store(test_corpus, "test_repo")
    print("   ✅ Collection created successfully")
    
    # Test 3: Test retrieval
    print("3. Testing retrieval...")
    results = retrieve(collection, "What does this project do?", k=2)
    print(f"   ✅ Retrieved {len(results)} results")
    for i, result in enumerate(results):
        print(f"     - Result {i+1}: {result['path']} (similarity: {result['similarity']})")
    
    print("\n🎉 All tests passed! The RAG system is working correctly.")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()