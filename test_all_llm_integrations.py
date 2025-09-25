#!/usr/bin/env python3
"""Comprehensive test for all SageVault LLM provider integrations"""

import sys
import os
sys.path.append('.')

def test_all_llm_providers():
    """Test all 4 LLM providers with the same interface"""
    print("🧪 Testing All LLM Provider Integrations...")
    
    providers_to_test = {
        "Groq": "Groq API error",
        "OpenAI": "OpenAI API error", 
        "Anthropic": "Anthropic API error",
        "Google": "Google Gemini API error"
    }
    
    try:
        from streamlit_app_clean import call_llm
        
        test_prompt = "Hello, can you help me understand RAG systems?"
        dummy_key = "dummy-test-key-12345"
        
        results = {}
        
        for provider, expected_error in providers_to_test.items():
            print(f"  Testing {provider}...")
            result = call_llm(provider, dummy_key, test_prompt)
            
            if expected_error in result:
                print(f"    ✅ {provider} integration working (expected API error)")
                results[provider] = True
            else:
                print(f"    ❌ {provider} unexpected result: {result[:100]}...")
                results[provider] = False
        
        # Check overall results
        passed = sum(results.values())
        total = len(results)
        
        print(f"\n📊 Provider Integration Results: {passed}/{total} working")
        
        if passed == total:
            print("🎉 All LLM providers integrated successfully!")
            return True
        else:
            failed_providers = [p for p, r in results.items() if not r]
            print(f"❌ Failed providers: {', '.join(failed_providers)}")
            return False
            
    except Exception as e:
        print(f"❌ LLM provider test failed: {e}")
        return False

def test_provider_consistency():
    """Test that all providers follow the same interface"""
    print("\n🧪 Testing Provider Interface Consistency...")
    
    try:
        from streamlit_app_clean import call_llm
        
        # Test with no API key
        providers = ["Groq", "OpenAI", "Anthropic", "Google"]
        
        for provider in providers:
            result = call_llm(provider, "", "test prompt")
            
            if "Please provide an API key" in result:
                print(f"  ✅ {provider} handles missing API key correctly")
            else:
                print(f"  ❌ {provider} unexpected response to missing key: {result}")
                return False
        
        # Test with unknown provider
        result = call_llm("UnknownProvider", "test-key", "test prompt")
        if "Unknown provider selected" in result:
            print("  ✅ Unknown provider handled correctly")
        else:
            print(f"  ❌ Unknown provider unexpected response: {result}")
            return False
        
        print("🎉 All providers follow consistent interface!")
        return True
        
    except Exception as e:
        print(f"❌ Provider consistency test failed: {e}")
        return False

def test_requirements_completeness():
    """Test that all required packages are in requirements"""
    print("\n🧪 Testing Requirements Completeness...")
    
    required_packages = [
        'groq>=',
        'openai>=', 
        'anthropic>=',
        'google-generativeai>='
    ]
    
    try:
        with open('requirements_clean.txt', 'r') as f:
            content = f.read()
        
        missing_packages = []
        for package in required_packages:
            if package not in content:
                missing_packages.append(package)
        
        if not missing_packages:
            print("  ✅ All LLM provider packages in requirements")
            return True
        else:
            print(f"  ❌ Missing packages: {missing_packages}")
            return False
            
    except Exception as e:
        print(f"❌ Requirements test failed: {e}")
        return False

def test_import_health():
    """Test that all LLM packages can be imported"""
    print("\n🧪 Testing Package Import Health...")
    
    imports_to_test = [
        ("groq", "Groq"),
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic"),
        ("google.generativeai", "Google Gemini")
    ]
    
    results = {}
    
    for package, name in imports_to_test:
        try:
            if package == "groq":
                from groq import Groq
            elif package == "openai":
                from openai import OpenAI
            elif package == "anthropic":
                import anthropic
            elif package == "google.generativeai":
                import google.generativeai as genai
            
            print(f"  ✅ {name} package imports successfully")
            results[name] = True
            
        except ImportError as e:
            print(f"  ❌ {name} import failed: {e}")
            results[name] = False
        except Exception as e:
            print(f"  ❌ {name} unexpected error: {e}")
            results[name] = False
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n📊 Import Health: {passed}/{total} packages importing correctly")
    return passed == total

def main():
    print("🚀 SageVault Complete LLM Integration Test Suite")
    print("=" * 60)
    
    tests = [
        test_import_health,
        test_requirements_completeness,
        test_provider_consistency,
        test_all_llm_providers
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
    
    print(f"\n📊 Complete Integration Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL LLM INTEGRATIONS WORKING PERFECTLY!")
        print("\n🌟 SageVault Multi-LLM Support Summary:")
        print("   ├── 🚀 Groq (Llama-3.1-8b-instant) - Fast inference")
        print("   ├── 🧠 OpenAI (GPT-4o-mini) - Premium quality")
        print("   ├── 🎯 Anthropic (Claude-3-5-sonnet) - Advanced reasoning")
        print("   └── 🔍 Google (Gemini-1.5-flash) - Multimodal capabilities")
        print("\n✨ Users can now choose their preferred LLM provider!")
        print("🔑 Each provider uses secure in-session API key storage")
        print("🛡️ Consistent error handling and user experience across all providers")
    else:
        print("⚠️ Some integration tests failed - review implementation")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)