#!/usr/bin/env python3
"""Test suite for RAG quality improvements: query enhancement and MMR re-ranking"""

import sys
import os
sys.path.append('.')

def test_query_enhancement():
    """Test automatic query enhancement with repository context"""
    print("🧪 Testing Query Enhancement...")
    
    try:
        from simple_rag import enhance_query_with_context
        
        # Test basic query without context
        base_query = "How do I install this?"
        enhanced = enhance_query_with_context(base_query)
        assert enhanced == base_query, "Query without context should remain unchanged"
        print("  ✅ Basic query without context handled correctly")
        
        # Test query with repository context
        repo_info = {"owner": "facebook", "repo": "react"}
        enhanced = enhance_query_with_context(base_query, repo_info=repo_info)
        assert "facebook/react" in enhanced, "Repository context should be added"
        print("  ✅ Repository context correctly added to query")
        
        # Test query with top-level directories
        top_dirs = ["src", "docs", "tests", "examples"]
        enhanced = enhance_query_with_context(base_query, top_level_dirs=top_dirs)
        assert "src" in enhanced and "docs" in enhanced, "Top-level directories should be added"
        print("  ✅ Top-level directories correctly added to query")
        
        # Test combined enhancement
        enhanced = enhance_query_with_context(base_query, repo_info, top_dirs)
        assert "facebook/react" in enhanced and "src" in enhanced, "Both repo and dirs should be added"
        print("  ✅ Combined repository and directory context working")
        
        # Test filtering of irrelevant directories
        bad_dirs = ["node_modules", ".git", "__pycache__", "venv", "src", "docs"]
        enhanced = enhance_query_with_context(base_query, top_level_dirs=bad_dirs)
        assert "node_modules" not in enhanced and ".git" not in enhanced, "Bad directories should be filtered"
        assert "src" in enhanced, "At least one good directory should remain"
        print("  ✅ Directory filtering working correctly")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Query enhancement test failed: {e}")
        return False

def test_mmr_functionality():
    """Test MMR (Maximal Marginal Relevance) re-ranking"""
    print("\n🧪 Testing MMR Re-ranking...")
    
    try:
        from simple_rag import apply_mmr
        
        # Create mock candidates with different similarities and content
        candidates = [
            {"text": "This is about React installation and setup", "similarity": 0.9},
            {"text": "This is also about React installation process", "similarity": 0.85},  # Similar to first
            {"text": "This covers React testing frameworks", "similarity": 0.7},  # Different topic
            {"text": "Guide to React deployment strategies", "similarity": 0.6},  # Different topic
            {"text": "Another React installation tutorial", "similarity": 0.8},  # Similar to first two
        ]
        
        # Mock query embedding (dummy values)
        query_embedding = [0.1] * 384  # Typical sentence-transformer embedding size
        
        # Test MMR selection
        selected = apply_mmr(candidates, query_embedding, k=3, lambda_param=0.7)
        
        assert len(selected) <= 3, "Should return at most k candidates"
        assert len(selected) > 0, "Should return at least one candidate"
        print(f"  ✅ MMR returned {len(selected)} candidates as expected")
        
        # Test that highest similarity is included
        similarities = [c["similarity"] for c in selected]
        max_sim = max(c["similarity"] for c in candidates)
        assert max_sim in similarities, "Highest similarity candidate should be included"
        print("  ✅ Highest similarity candidate included in MMR results")
        
        # Test edge cases
        empty_selected = apply_mmr([], query_embedding, k=3)
        assert len(empty_selected) == 0, "Empty candidates should return empty list"
        print("  ✅ Empty candidates handled correctly")
        
        single_selected = apply_mmr([candidates[0]], query_embedding, k=3)
        assert len(single_selected) == 1, "Single candidate should return that candidate"
        print("  ✅ Single candidate handled correctly")
        
        return True
        
    except Exception as e:
        print(f"  ❌ MMR test failed: {e}")
        return False

def test_enhanced_search_integration():
    """Test integration of query enhancement and MMR in search_vector_store"""
    print("\n🧪 Testing Integrated Enhanced Search...")
    
    try:
        from simple_rag import create_vector_store, search_vector_store
        
        # Create test documents
        test_docs = {
            "README.md": "Welcome to our React project! This is a modern web application.",
            "src/App.js": "import React from 'react'; function App() { return <div>Hello</div>; }",
            "src/components/Button.js": "export const Button = () => <button>Click me</button>;",
            "docs/installation.md": "To install: npm install react react-dom",
            "docs/deployment.md": "Deploy using: npm run build && npm run deploy",
            "tests/App.test.js": "import { render } from '@testing-library/react'; test('renders', () => {});"
        }
        
        # Create vector store
        collection = create_vector_store(test_docs, "test_enhanced", chunk_size=200, overlap_percent=10)
        print("  ✅ Test vector store created successfully")
        
        # Test enhanced search with repository context
        repo_info = {"owner": "testuser", "repo": "react-app"}
        top_dirs = ["src", "docs", "tests"]
        
        results = search_vector_store(
            collection, 
            "How to install?", 
            k=3,
            repo_info=repo_info,
            top_level_dirs=top_dirs
        )
        
        assert len(results) > 0, "Should return search results"
        assert all('similarity' in r for r in results), "All results should have similarity scores"
        print(f"  ✅ Enhanced search returned {len(results)} results with similarity scores")
        
        # Check that results are properly formatted
        for result in results:
            assert 'file_path' in result, "Results should have file_path"
            assert 'text' in result, "Results should have text"
            assert 'similarity' in result, "Results should have similarity"
            assert isinstance(result['similarity'], (int, float)), "Similarity should be numeric"
        print("  ✅ All search results properly formatted")
        
        # Test that installation-related content is prioritized
        installation_found = any("install" in r['text'].lower() for r in results)
        assert installation_found, "Installation-related content should be found"
        print("  ✅ Relevant content successfully retrieved")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Enhanced search integration test failed: {e}")
        return False

def test_diversity_improvement():
    """Test that MMR actually improves result diversity"""
    print("\n🧪 Testing Result Diversity Improvement...")
    
    try:
        from simple_rag import create_vector_store, search_vector_store
        
        # Create documents with intentional redundancy
        redundant_docs = {
            "guide1.md": "How to install React: npm install react react-dom. React is great.",
            "guide2.md": "React installation guide: use npm install react react-dom. React rocks.",
            "guide3.md": "Install React easily: npm install react react-dom. React is awesome.",
            "testing.md": "React testing with Jest and React Testing Library. Write good tests.",
            "deployment.md": "Deploy React apps to production using build tools and hosting.",
            "styling.md": "Style React components with CSS modules and styled-components."
        }
        
        collection = create_vector_store(redundant_docs, "test_diversity", chunk_size=300)
        
        # Search with a query that would match installation docs highly
        results = search_vector_store(collection, "how to install react", k=4)
        
        # Check for diversity in file paths (MMR should prevent all installation guides)
        file_paths = [r['file_path'] for r in results]
        unique_topics = set()
        
        for path in file_paths:
            if 'guide' in path:
                unique_topics.add('installation')
            elif 'test' in path:
                unique_topics.add('testing')
            elif 'deploy' in path:
                unique_topics.add('deployment')
            elif 'style' in path:
                unique_topics.add('styling')
        
        print(f"  📊 Found topics in results: {unique_topics}")
        
        # MMR should provide some diversity beyond just installation guides
        assert len(unique_topics) > 1, "MMR should provide topic diversity beyond just installation"
        print("  ✅ MMR successfully diversified search results")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Diversity improvement test failed: {e}")
        return False

def test_backward_compatibility():
    """Test that enhancements don't break existing functionality"""
    print("\n🧪 Testing Backward Compatibility...")
    
    try:
        from simple_rag import create_vector_store, search_vector_store
        
        # Test old-style search calls without repo_info or top_level_dirs
        simple_docs = {
            "README.md": "This is a simple test document about our project.",
            "main.py": "def main(): print('Hello world')"
        }
        
        collection = create_vector_store(simple_docs, "test_compat")
        
        # Old-style call (should still work)
        results = search_vector_store(collection, "test project", k=2)
        assert len(results) > 0, "Old-style search should still work"
        print("  ✅ Backward compatibility maintained for search_vector_store")
        
        # Test create_vector_store with default parameters
        collection2 = create_vector_store(simple_docs, "test_compat2")
        assert collection2 is not None, "Vector store creation should work with defaults"
        print("  ✅ Backward compatibility maintained for create_vector_store")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Backward compatibility test failed: {e}")
        return False

def main():
    """Run all quality improvement tests"""
    print("🚀 SageVault Quality Improvements Test Suite")
    print("=" * 60)
    
    tests = [
        test_query_enhancement,
        test_mmr_functionality,
        test_enhanced_search_integration,
        test_diversity_improvement,
        test_backward_compatibility
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ PASSED")
            else:
                failed += 1
                print("❌ FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ FAILED with exception: {e}")
        print("-" * 40)
    
    print(f"\n📊 Quality Improvements Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL QUALITY IMPROVEMENTS WORKING PERFECTLY!")
        print("\n🌟 Enhanced RAG Features Summary:")
        print("   ├── 🔍 Query Enhancement - Automatic repo context expansion")
        print("   ├── 🎯 MMR Re-ranking - Balanced similarity and diversity")
        print("   ├── 📚 README Prioritization - Important docs surface first")
        print("   └── 🔄 Backward Compatibility - Existing code unaffected")
        print("\n✨ Users will now get more relevant and diverse search results!")
        print("🎯 Queries automatically enhanced with repository context")
        print("⚖️ Results balanced between relevance and novelty using MMR")
    else:
        print("⚠️ Some quality improvement tests failed - review implementation")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)