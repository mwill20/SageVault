#!/usr/bin/env python3
"""Smoke test for Google Gemini integration in SageVault"""

import sys
import os
sys.path.append('.')

def test_gemini_import():
    """Test that google-generativeai package imports correctly"""
    print("🧪 Testing Google GenerativeAI import...")
    try:
        import google.generativeai as genai
        print(f"✅ Google GenerativeAI package imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import google.generativeai: {e}")
        return False

def test_gemini_integration():
    """Test Gemini integration in call_llm function"""
    print("\n🧪 Testing Gemini integration...")
    
    try:
        from streamlit_app_clean import call_llm
        
        # Test with dummy API key (should fail gracefully)
        result = call_llm("Google", "dummy-key-test", "Hello, this is a test.")
        
        if "Google Gemini API error" in result:
            print("✅ Gemini integration works (got expected API error with dummy key)")
            return True
        else:
            print(f"❓ Unexpected result: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Gemini integration test failed: {e}")
        return False

def test_provider_selection():
    """Test that Google is available in provider selection"""
    print("\n🧪 Testing provider selection...")
    
    try:
        # Since we can't easily test Streamlit selectbox, we'll check the code
        with open('streamlit_app_clean.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '"Google"' in content and 'selectbox' in content:
            print("✅ Google provider available in selectbox")
            return True
        else:
            print("❌ Google provider not found in selectbox")
            return False
            
    except Exception as e:
        print(f"❌ Provider selection test failed: {e}")
        return False

def test_requirements_updated():
    """Test that requirements_clean.txt includes google-generativeai"""
    print("\n🧪 Testing requirements update...")
    
    try:
        with open('requirements_clean.txt', 'r') as f:
            content = f.read()
        
        if 'google-generativeai>=' in content:
            print("✅ google-generativeai package added to requirements_clean.txt")
            return True
        else:
            print("❌ google-generativeai package not found in requirements")
            return False
            
    except Exception as e:
        print(f"❌ Requirements test failed: {e}")
        return False

def test_all_providers():
    """Test that all 4 providers are available"""
    print("\n🧪 Testing complete provider lineup...")
    
    try:
        with open('streamlit_app_clean.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        expected_providers = ['"Groq"', '"OpenAI"', '"Anthropic"', '"Google"']
        found_providers = []
        
        for provider in expected_providers:
            if provider in content:
                found_providers.append(provider)
        
        if len(found_providers) == 4:
            print(f"✅ All 4 LLM providers available: {', '.join(found_providers)}")
            return True
        else:
            print(f"❌ Missing providers. Found: {', '.join(found_providers)}")
            return False
            
    except Exception as e:
        print(f"❌ All providers test failed: {e}")
        return False

def main():
    print("🚀 SageVault Gemini Integration Smoke Test")
    print("=" * 50)
    
    tests = [
        test_gemini_import,
        test_gemini_integration,
        test_provider_selection,
        test_requirements_updated,
        test_all_providers
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
    
    print(f"\n📊 Gemini Integration Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All Gemini integration tests passed!")
        print("🔑 Ready to test with real Google AI API key")
        print("🌟 SageVault now supports 4 LLM providers:")
        print("   • Groq (Llama-3.1-8b-instant)")
        print("   • OpenAI (GPT-4o-mini)")
        print("   • Anthropic (Claude-3-5-sonnet)")
        print("   • Google (Gemini-1.5-flash)")
    else:
        print("⚠️ Some tests failed - review implementation")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)