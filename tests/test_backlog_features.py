"""
🧪 Test Suite for Backlog Features
Performance monitoring and session export functionality validation
"""

import time
import tempfile
import os
from monitoring.performance_monitor import PerformanceMonitor, ProviderMetrics, track_llm_request
from utilities.session_exporter import SessionExporter, CitedSource, QASession

def test_performance_monitoring():
    """Test the performance monitoring system"""
    print("🧪 Testing Performance Monitoring...")
    
    # Create monitor instance
    monitor = PerformanceMonitor()
    
    # Test tracking decorator
    @monitor.track_request('openai')
    def mock_openai_call():
        time.sleep(0.1)  # Simulate API call
        # Mock response with usage data
        class MockUsage:
            prompt_tokens = 1500
            completion_tokens = 800
        
        class MockResponse:
            usage = MockUsage()
        
        return MockResponse()
    
    # Test request tracking
    result = mock_openai_call()
    
    # Verify metrics were stored
    assert 'openai' in monitor.metrics
    assert len(monitor.metrics['openai']) == 1
    
    metric = monitor.metrics['openai'][0]
    assert metric.provider == 'openai'
    assert metric.latency_ms > 100  # Should be around 100ms
    assert metric.tokens_in == 1500
    assert metric.tokens_out == 800
    assert metric.estimated_cost is not None
    
    # Test badge generation
    badge = monitor.get_provider_badge('openai')
    assert 'OpenAI:' in badge
    assert 'ms' in badge
    assert '$' in badge
    
    print("  ✅ Performance tracking working correctly")
    print(f"  ✅ Generated badge: {badge}")
    
    # Test session summary
    summary = monitor.get_session_summary()
    assert 'providers' in summary
    assert 'openai' in summary['providers']
    assert summary['providers']['openai']['requests'] == 1
    
    print("  ✅ Session summary generated correctly")
    return True

def test_session_export():
    """Test the session export functionality"""
    print("🧪 Testing Session Export...")
    
    # Create exporter instance
    exporter = SessionExporter()
    exporter.set_repository_url("https://github.com/test/sagevault")
    
    # Add test sessions
    exporter.add_session(
        question="How does authentication work in this system?",
        answer="The authentication system uses JWT tokens with middleware validation. The process involves token generation, validation, and refresh mechanisms.",
        provider="openai",
        sources=[
            {
                'filename': 'src/auth/middleware.py',
                'similarity_score': 0.92,
                'content': 'def validate_jwt_token(token):\n    """Validate JWT token and extract user info"""\n    try:\n        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])\n        return payload\n    except jwt.ExpiredSignatureError:\n        raise AuthError("Token expired")',
                'line_numbers': '25-35'
            },
            {
                'filename': 'src/auth/tokens.py',
                'similarity_score': 0.88,
                'content': 'def generate_access_token(user_id: int) -> str:\n    """Generate JWT access token for user"""\n    payload = {\n        "user_id": user_id,\n        "exp": datetime.utcnow() + timedelta(hours=1),\n        "iat": datetime.utcnow()\n    }\n    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")',
                'line_numbers': '10-20'
            }
        ],
        performance_metrics={
            'latency_ms': 1200,
            'tokens_in': 1500,
            'tokens_out': 800,
            'estimated_cost': 0.0024
        }
    )
    
    exporter.add_session(
        question="What are the main security considerations?",
        answer="The main security considerations include input validation, SQL injection prevention, XSS protection, and secure session management.",
        provider="anthropic",
        sources=[
            {
                'filename': 'src/security/validators.py',
                'similarity_score': 0.85,
                'content': 'def sanitize_input(user_input: str) -> str:\n    """Sanitize user input to prevent XSS attacks"""\n    # Remove script tags and dangerous HTML\n    cleaned = re.sub(r\'<script.*?</script>\', \'\', user_input, flags=re.IGNORECASE)\n    return html.escape(cleaned)',
                'line_numbers': '40-50'
            }
        ],
        performance_metrics={
            'latency_ms': 2100,
            'tokens_in': 1200,
            'tokens_out': 650,
            'estimated_cost': 0.0135
        }
    )
    
    # Test markdown export
    markdown = exporter.export_to_markdown(title="Test Session Export")
    
    # Debug: Print markdown to see what we're getting
    print("  🔍 Generated markdown preview:")
    print(markdown[:500] + "..." if len(markdown) > 500 else markdown)
    
    # Verify markdown content
    assert "# Test Session Export" in markdown
    assert "## Q&A Session 1" in markdown
    assert "## Q&A Session 2" in markdown
    assert "How does authentication work" in markdown
    assert "What are the main security considerations" in markdown
    assert "src/auth/middleware.py" in markdown
    assert "src/security/validators.py" in markdown
    assert "92.0%" in markdown  # Similarity score
    assert "OpenAI" in markdown
    assert "Anthropic" in markdown
    assert "$0.002" in markdown  # Cost
    assert "1200ms" in markdown  # Latency
    
    print("  ✅ Markdown export generated correctly")
    
    # Test file export
    with tempfile.TemporaryDirectory() as temp_dir:
        filename = os.path.join(temp_dir, "test_export.md")
        saved_filename = exporter.save_to_file(filename, "Test Export")
        
        assert os.path.exists(saved_filename)
        
        with open(saved_filename, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "# Test Export" in content
            assert len(content) > 1000  # Should be substantial content
    
    print("  ✅ File export working correctly")
    
    # Test GitHub URL generation
    github_url = exporter._generate_github_url("src/auth/middleware.py")
    expected = "https://github.com/test/sagevault/blob/main/src/auth/middleware.py"
    assert github_url == expected
    
    print("  ✅ GitHub URL generation working correctly")
    return True

def test_integration_workflow():
    """Test integrated workflow of performance monitoring + session export"""
    print("🧪 Testing Integration Workflow...")
    
    monitor = PerformanceMonitor()
    exporter = SessionExporter()
    exporter.set_repository_url("https://github.com/test/integration")
    
    # Simulate a complete workflow
    @monitor.track_request('groq')
    def simulate_rag_query():
        time.sleep(0.05)  # Fast Groq response
        class MockResponse:
            x_groq = {'usage': {'prompt_tokens': 800, 'completion_tokens': 300}}
        return MockResponse()
    
    # Execute RAG query
    result = simulate_rag_query()
    
    # Get performance metrics
    metrics = monitor.get_session_summary()['providers']['groq']
    
    # Add to session export with performance data
    exporter.add_session(
        question="Test integration question",
        answer="Integrated response with performance tracking",
        provider="groq",
        sources=[{
            'filename': 'test/integration.py',
            'similarity_score': 0.95,
            'content': 'def test_function():\n    pass',
            'line_numbers': '1-2'
        }],
        performance_metrics={
            'latency_ms': metrics['avg_latency_ms'],
            'tokens_in': metrics['total_tokens_in'],
            'tokens_out': metrics['total_tokens_out'],
            'estimated_cost': metrics['total_cost']
        }
    )
    
    # Generate comprehensive export
    markdown = exporter.export_to_markdown(title="Integration Test Results", include_performance=True)
    
    # Verify integration
    assert "Groq" in markdown
    assert "95.0%" in markdown
    assert "ms" in markdown
    assert "test/integration.py" in markdown
    
    print("  ✅ Integration workflow completed successfully")
    return True

def run_all_tests():
    """Run comprehensive test suite for backlog features"""
    print("🚀 SageVault Backlog Features Test Suite")
    print("=" * 60)
    
    tests = [
        test_performance_monitoring,
        test_session_export,
        test_integration_workflow
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
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
        print("-" * 40)
    
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL BACKLOG FEATURES WORKING!")
        print()
        print("🌟 Features Successfully Implemented:")
        print("   ├── 📊 Provider Cost/Latency Tracking")
        print("   ├── 💰 Token Usage & Cost Estimation")
        print("   ├── 📱 Performance Badge Generation")
        print("   ├── 📝 Session Export to Markdown")
        print("   ├── 🔗 GitHub Link Integration")
        print("   └── 🧪 Comprehensive Test Coverage")
        print()
        print("✨ Ready for integration into main application!")
    
    return failed == 0

if __name__ == "__main__":
    run_all_tests()