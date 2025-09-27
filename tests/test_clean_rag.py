#!/usr/bin/env python3
"""Test the clean RAG implementation"""

print("Testing clean RAG implementation...")

try:
    from simple_rag import create_vector_store, search_vector_store
    print("✅ Imports successful")
    
    # Test data
    test_docs = {
        "README.md": """# Clean RAG Test
        
This is a test project for the clean RAG implementation.
It demonstrates how to build a simple but effective retrieval system.

## Features
- Vector search using ChromaDB
- Sentence transformers for embeddings
- Simple chunking strategy
""",
        "main.py": """def hello_world():
    print("Hello from the clean RAG system!")
    return "success"

if __name__ == "__main__":
    result = hello_world()
    print(f"Result: {result}")
"""
    }
    
    # Create vector store
    print("Creating vector store...")
    collection = create_vector_store(test_docs, "test_clean")
    print("✅ Vector store created")
    
    # Test search
    print("Testing search...")
    results = search_vector_store(collection, "What is this project about?", k=3)
    print(f"✅ Found {len(results)} results")
    
    for i, result in enumerate(results):
        print(f"  Result {i+1}: {result['file_path']} (similarity: {result['similarity']})")
        print(f"    Text: {result['text'][:100]}...")
    
    print("\n🎉 Clean RAG implementation working perfectly!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()