#!/usr/bin/env python3
"""Smoke test for Anthropic Claude integration in SageVault"""

import sys
import os
sys.path.append('.')

def test_claude_import():
    """Test that anthropic package imports correctly"""
    print("🧪 Testing Anthropic import...")
    try:
        import anthropic
        print(f"✅ Anthropic package imported successfully (version available)")
        return True
    except ImportError as e:
        print(f"❌ Failed to import anthropic: {e}")
        return False

def test_claude_integration():
    """Test Claude integration in call_llm function"""
    print("\n🧪 Testing Claude integration...")
    
    try:
        from streamlit_app_clean import call_llm
        
        # Test with dummy API key (should fail gracefully)
        result = call_llm("Anthropic", "dummy-key-test", "Hello, this is a test.")
        
        if "Anthropic API error" in result:
            print("✅ Claude integration works (got expected API error with dummy key)")
            return True
        else:
            print(f"❓ Unexpected result: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Claude integration test failed: {e}")
        return False

def test_provider_selection():
    """Test that Anthropic is available in provider selection"""
    print("\n🧪 Testing provider selection...")
    
    try:
        # Since we can't easily test Streamlit selectbox, we'll check the code
        with open('streamlit_app_clean.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '"Anthropic"' in content and 'selectbox' in content:
            print("✅ Anthropic provider available in selectbox")
            return True
        else:
            print("❌ Anthropic provider not found in selectbox")
            return False
            
    except Exception as e:
        print(f"❌ Provider selection test failed: {e}")
        return False

def test_requirements_updated():
    """Test that requirements_clean.txt includes anthropic"""
    print("\n🧪 Testing requirements update...")
    
    try:
        with open('requirements_clean.txt', 'r') as f:
            content = f.read()
        
        if 'anthropic>=' in content:
            print("✅ anthropic package added to requirements_clean.txt")
            return True
        else:
            print("❌ anthropic package not found in requirements")
            return False
            
    except Exception as e:
        print(f"❌ Requirements test failed: {e}")
        return False

def main():
    print("🚀 SageVault Claude Integration Smoke Test")
    print("=" * 50)
    
    tests = [
        test_claude_import,
        test_claude_integration,
        test_provider_selection,
        test_requirements_updated
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
        print("-" * 30)
    
    print(f"\n📊 Claude Integration Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All Claude integration tests passed!")
        print("🔑 Ready to test with real Anthropic API key")
    else:
        print("⚠️ Some tests failed - review implementation")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)