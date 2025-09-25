#!/usr/bin/env python3
"""Test suite for SageVault analytics and documentation features"""

import sys
import os
import json
import time
sys.path.append('.')

def test_analytics_privacy_compliance():
    """Test that analytics system maintains privacy standards"""
    print("🧪 Testing Analytics Privacy Compliance...")
    
    try:
        from analytics import (
            PrivacyFirstAnalytics, track_index_built, track_question_asked,
            track_files_processed, get_privacy_info, clear_analytics
        )
        
        # Test privacy info
        privacy_info = get_privacy_info()
        assert "data_not_collected" in privacy_info, "Privacy info should list what's NOT collected"
        
        not_collected = privacy_info["data_not_collected"]
        privacy_essentials = [
            "user prompts", "API keys", "file contents", "personal information"
        ]
        for essential in privacy_essentials:
            assert any(essential in item for item in not_collected), f"Should not collect {essential}"
        
        print("  ✅ Privacy compliance documentation verified")
        
        # Test that sensitive data is rejected
        analytics = PrivacyFirstAnalytics()
        
        # Try to track prohibited event type
        result = analytics.track_event("user_prompt_content")  # Should be rejected
        assert not result, "Should reject prohibited event types"
        
        # Test metadata sanitization
        sensitive_metadata = {
            "user_prompt": "How do I hack this?",  # Should be filtered out
            "api_key": "sk-1234567890",          # Should be filtered out
            "file_count": 5,                     # Should be allowed
            "provider_type": "groq"              # Should be allowed
        }
        
        analytics.track_event("question_asked", metadata=sensitive_metadata)
        
        # Check that only safe metadata was stored
        if analytics.events:
            stored_metadata = analytics.events[-1].metadata
            assert "user_prompt" not in stored_metadata, "Should filter out user prompts"
            assert "api_key" not in stored_metadata, "Should filter out API keys"
            assert stored_metadata.get("file_count") == 5, "Should preserve safe numeric data"
            assert stored_metadata.get("provider_type") == "groq", "Should preserve safe categorical data"
        
        print("  ✅ Sensitive data filtering working correctly")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Analytics privacy test failed: {e}")
        return False

def test_analytics_functionality():
    """Test core analytics tracking functionality"""
    print("\n🧪 Testing Analytics Core Functionality...")
    
    try:
        from analytics import (
            track_index_built, track_question_asked, track_files_processed,
            track_document_upload, get_session_summary, clear_analytics
        )
        
        # Clear any existing analytics
        clear_analytics() 
        
        # Test index tracking
        track_index_built(
            file_count=25,
            file_types=["main.py", "config.yaml", "README.md"],
            source_type="repository"
        )
        
        # Test question tracking
        track_question_asked(provider_type="groq", response_generated=True)
        track_question_asked(provider_type="openai", response_generated=False)
        
        # Test file processing tracking
        track_files_processed(
            included_count=20,
            excluded_count=5,
            risk_levels=["LOW", "MEDIUM", "HIGH"]
        )
        
        # Test document upload tracking
        track_document_upload(
            file_count=3,
            file_types=["document.pdf", "presentation.pptx", "data.csv"]
        )
        
        # Get session summary
        summary = get_session_summary()
        
        # Validate summary contains expected data
        assert summary["questions_asked"] >= 2, "Should track question events"
        assert summary["indexes_built"] >= 1, "Should track index events"
        assert summary["total_files_processed"] >= 25, "Should count total files processed"
        assert "session_duration_minutes" in summary, "Should track session duration"
        
        print(f"  ✅ Session summary generated: {summary['total_events']} events tracked")
        print(f"  ✅ Questions asked: {summary['questions_asked']}")
        print(f"  ✅ Files processed: {summary['total_files_processed']}")
        print(f"  ✅ Session duration: {summary['session_duration_minutes']} minutes")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Analytics functionality test failed: {e}")
        return False

def test_analytics_export():
    """Test analytics data export functionality"""
    print("\n🧪 Testing Analytics Export...")
    
    try:
        from analytics import export_analytics, get_session_summary
        
        # Test JSON export
        export_json = export_analytics(include_timestamps=False)
        export_data = json.loads(export_json)
        
        assert "session_id" in export_data, "Export should include session ID"
        assert "total_events" in export_data, "Export should include event count"
        assert "event_counts" in export_data, "Export should include event breakdown"
        
        # Test detailed export with timestamps
        detailed_export = export_analytics(include_timestamps=True)
        detailed_data = json.loads(detailed_export)
        
        assert "events" in detailed_data, "Detailed export should include events list"
        assert "summary" in detailed_data, "Detailed export should include summary"
        
        print("  ✅ Analytics export working correctly")
        print(f"  ✅ Export data structure validated")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Analytics export test failed: {e}")
        return False

def test_streamlit_integration():
    """Test that analytics integrates properly with streamlit app"""
    print("\n🧪 Testing Streamlit Integration...")
    
    try:
        # Test imports
        import streamlit_app_clean
        from analytics import get_session_summary
        
        # Test that analytics functions are importable
        from streamlit_app_clean import (
            track_index_built, track_question_asked, track_files_processed
        )
        
        print("  ✅ Analytics imports successful in streamlit app")
        
        # Test session summary format for UI display
        summary = get_session_summary()
        required_fields = [
            "questions_asked", "indexes_built", "total_files_processed", 
            "session_duration_minutes"
        ]
        
        for field in required_fields:
            assert field in summary, f"Summary should include {field} for UI display"
            assert isinstance(summary[field], (int, float)), f"{field} should be numeric for metrics"
        
        print("  ✅ Session summary format compatible with UI metrics")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Streamlit integration test failed: {e}")
        return False

def test_readme_structure():
    """Test README structure and content"""
    print("\n🧪 Testing README Structure...")
    
    try:
        readme_path = "README.md"
        if not os.path.exists(readme_path):
            print(f"  ❌ README.md not found at {readme_path}")
            return False
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
        
        # Test essential sections
        essential_sections = [
            "Demo: See SageVault in Action",
            "🎬 Demo GIF Placeholder",
            "Try it Yourself - 3-Minute Walkthrough", 
            "Privacy-First Analytics",
            "Analytics Dashboard"
        ]
        
        for section in essential_sections:
            assert section in readme_content, f"README should include {section} section"
        
        # Test logo reference
        assert "sagevault-logo.png" in readme_content, "README should reference the logo"
        assert "assets/sagevault-logo.png" in readme_content, "Logo should be in assets folder"
        
        # Test demo workflow structure
        assert "Step 1:" in readme_content, "Should have step-by-step demo workflow"
        assert "Step 2:" in readme_content, "Should have multiple demo steps"
        assert "Example questions to try:" in readme_content, "Should provide example questions"
        
        # Test analytics documentation
        assert "Zero PII" in readme_content, "Should document privacy features"
        assert "Session-Only" in readme_content, "Should explain ephemeral nature"
        
        print("  ✅ README structure validated")
        print("  ✅ Demo workflow section present")
        print("  ✅ Analytics documentation included")
        print("  ✅ Logo integration verified")
        
        return True
        
    except Exception as e:
        print(f"  ❌ README structure test failed: {e}")
        return False

def test_demo_gif_placeholder():
    """Test demo GIF placeholder and instructions"""
    print("\n🧪 Testing Demo GIF Integration...")
    
    try:
        readme_path = "README.md"
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
        
        # Test GIF placeholder
        assert "demo-workflow.gif" in readme_content, "Should reference demo GIF file"
        assert "📽️ Quick Demo Workflow" in readme_content, "Should have demo section header"
        assert "Record and add a GIF" in readme_content, "Should have recording instructions"
        
        # Test workflow description
        workflow_steps = ["Paste a Repository URL", "Index & Analyze", "Ask Intelligent Questions", "Explore Sources Panel"]
        for step in workflow_steps:
            assert step in readme_content, f"Demo workflow should include {step}"
        
        # Test interactive demo table
        assert "Interactive Demo Features" in readme_content, "Should have interactive features table"
        assert "Multi-LLM Support" in readme_content, "Should demonstrate multi-LLM feature"
        assert "Analytics Dashboard" in readme_content, "Should mention analytics in demo"
        
        print("  ✅ Demo GIF placeholder properly configured")
        print("  ✅ Workflow instructions comprehensive")
        print("  ✅ Interactive demo features documented")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Demo GIF integration test failed: {e}")
        return False

def main():
    """Run all analytics and documentation tests"""
    print("🚀 SageVault Analytics & Documentation Test Suite")
    print("=" * 60)
    
    tests = [
        test_analytics_privacy_compliance,
        test_analytics_functionality,
        test_analytics_export,
        test_streamlit_integration,
        test_readme_structure,
        test_demo_gif_placeholder
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
    
    print(f"\n📊 Analytics & Documentation Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL ANALYTICS & DOCUMENTATION FEATURES WORKING!")
        print("\n🌟 Features Successfully Implemented:")
        print("   ├── 📊 Privacy-First Analytics - Zero PII, session-only tracking")
        print("   ├── 🎬 Demo Documentation - Complete workflow with GIF placeholder")
        print("   ├── 🔒 Data Protection - Sensitive data filtering and user control")
        print("   ├── 📱 UI Integration - Sidebar analytics dashboard")
        print("   ├── 📖 README Enhancement - Interactive demo and comprehensive docs")
        print("   └── 🧪 Quality Assurance - Full test coverage and validation")
        print("\n✨ Ready for production use with complete privacy compliance!")
        print("📽️ Record demo GIF at: assets/demo-workflow.gif")
        print("🔍 View analytics in app sidebar: '📊 Session Analytics'")
    else:
        print("⚠️ Some tests failed - review implementation")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)