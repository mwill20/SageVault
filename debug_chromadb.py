#!/usr/bin/env python3
"""Debug script to reproduce ChromaDB override decorator error"""

try:
    from app.rag_utils import build_store
    print("Successfully imported build_store")
    
    # Try to create a simple store
    test_corpus = {"test.py": "print('hello world')"}
    collection = build_store(test_corpus, "test")
    print("Successfully created ChromaDB collection")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()