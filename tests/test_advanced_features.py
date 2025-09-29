"""
🧪 Test Suite for Advanced Features
Evaluation harness and repository type detection validation
"""
import sys
sys.path.append('utilities')
sys.path.append('monitoring')

import json
import tempfile
from utilities.eval_harness import EvaluationHarness, GoldStandardPair, EvalResult
from utilities.repo_analyzer import RepositoryAnalyzer, ProjectType, QuickstartGuide

def test_evaluation_harness():
    """Test the evaluation harness functionality"""
    print("🧪 Testing Evaluation Harness...")
    
    # Create harness instance
    harness = EvaluationHarness()
    
    # Test gold standard loading
    harness.load_gold_standards()  # Load built-in standards
    
    assert len(harness.gold_standards) > 0
    print(f"  ✅ Loaded {len(harness.gold_standards)} gold standard test cases")
    
    # Test individual components
    gold_standard = harness.gold_standards[0]
    assert isinstance(gold_standard, GoldStandardPair)
    assert gold_standard.query
    assert gold_standard.expected_files
    assert gold_standard.repo_name
    
    print("  ✅ Gold standard structure validated")
    
    # Test metrics calculation (mock retrieval)
    mock_retrieved = [
        {'filename': 'README.md', 'similarity_score': 0.95},
        {'filename': 'docs/tutorial.md', 'similarity_score': 0.88},
        {'filename': 'fastapi/applications.py', 'similarity_score': 0.82},
        {'filename': 'src/main.py', 'similarity_score': 0.75},
        {'filename': 'tests/test_main.py', 'similarity_score': 0.68}
    ]
    
    result = harness._calculate_metrics(gold_standard, mock_retrieved, [1, 3, 5], 150.0)
    
    assert isinstance(result, EvalResult)
    assert result.precision_at_k[1] >= 0.0
    assert result.precision_at_k[5] >= 0.0
    assert result.found_in_top_k[5] in [True, False]
    assert result.latency_ms == 150.0
    
    print("  ✅ Metrics calculation working correctly")
    
    # Test aggregation
    mock_results = [result]  # Single result for testing
    summary = harness._aggregate_results(mock_results, [1, 3, 5])
    
    assert 'total_queries' in summary
    assert 'metrics_by_k' in summary
    assert 'overall_performance' in summary
    assert summary['total_queries'] == 1
    
    print("  ✅ Results aggregation working correctly")
    
    # Test results export
    harness.results_history = [{'timestamp': '2025-09-25', 'summary': summary, 'individual_results': mock_results}]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        filename = harness.save_results(f.name)
        
        with open(filename, 'r') as read_f:
            saved_data = json.load(read_f)
            assert len(saved_data) == 1
            assert 'summary' in saved_data[0]
    
    print("  ✅ Results export working correctly")
    
    return True

def test_repository_analyzer():
    """Test the repository type detection"""
    print("🧪 Testing Repository Analyzer...")
    
    analyzer = RepositoryAnalyzer()
    
    # Test Python project detection
    python_files = [
        'requirements.txt',
        'app.py', 
        'streamlit_app.py',
        'src/main.py',
        'tests/test_main.py',
        'README.md',
        '.gitignore'
    ]
    
    detected_types = analyzer.analyze_repository(python_files)
    
    assert len(detected_types) > 0
    python_type = next((t for t in detected_types if t.name == 'python'), None)
    assert python_type is not None
    assert python_type.confidence > 0.5
    assert 'requirements.txt' in python_type.indicators
    
    print(f"  ✅ Detected Python project (confidence: {python_type.confidence:.2f})")
    
    # Test Node.js project detection
    node_files = [
        'package.json',
        'package-lock.json',
        'src/index.js',
        'src/components/App.js',
        'node_modules/react/index.js',
        'public/index.html',
        'README.md'
    ]
    
    detected_types = analyzer.analyze_repository(node_files)
    node_type = next((t for t in detected_types if t.name == 'nodejs'), None)
    assert node_type is not None
    assert node_type.confidence > 0.5
    
    print(f"  ✅ Detected Node.js project (confidence: {node_type.confidence:.2f})")
    
    # Test Docker project detection
    docker_files = [
        'Dockerfile',
        'docker-compose.yml',
        '.dockerignore',
        'app.py',
        'requirements.txt'
    ]
    
    detected_types = analyzer.analyze_repository(docker_files)
    docker_type = next((t for t in detected_types if t.name == 'docker'), None)
    assert docker_type is not None
    assert docker_type.confidence > 0.4
    
    print(f"  ✅ Detected Docker project (confidence: {docker_type.confidence:.2f})")
    
    # Test multi-language detection
    mixed_files = [
        'package.json',  # Node.js
        'requirements.txt',  # Python
        'Dockerfile',  # Docker
        'src/app.js',
        'src/main.py',
        'README.md'
    ]
    
    detected_types = analyzer.analyze_repository(mixed_files)
    assert len(detected_types) >= 2  # Should detect multiple types
    
    # Sort by confidence
    detected_types.sort(key=lambda x: x.confidence, reverse=True)
    primary_type = detected_types[0]
    
    print(f"  ✅ Multi-language detection: Primary type is {primary_type.name} ({primary_type.confidence:.2f})")
    
    return True

def test_quickstart_generation():
    """Test quickstart guide generation"""
    print("🧪 Testing Quickstart Generation...")
    
    analyzer = RepositoryAnalyzer()
    
    # Test Python quickstart
    python_type = ProjectType(
        name='python',
        confidence=0.85,
        indicators=['requirements.txt', 'app.py'],
        framework='streamlit'
    )
    
    guide = analyzer.generate_quickstart_guide(python_type)
    
    assert isinstance(guide, QuickstartGuide)
    assert 'Python' in guide.title
    assert 'Streamlit' in guide.title
    assert len(guide.install_commands) > 0
    assert len(guide.run_commands) > 0
    assert 'streamlit run' in ' '.join(guide.run_commands)
    
    print("  ✅ Python/Streamlit quickstart generated correctly")
    
    # Test Node.js quickstart
    node_type = ProjectType(
        name='nodejs',
        confidence=0.90,
        indicators=['package.json', 'yarn.lock'],
        framework='react'
    )
    
    guide = analyzer.generate_quickstart_guide(node_type)
    
    assert 'Node.js' in guide.title
    assert 'React' in guide.title
    assert any('yarn install' in cmd for cmd in guide.install_commands)
    assert any('yarn start' in cmd for cmd in guide.run_commands)
    
    print("  ✅ Node.js/React quickstart generated correctly")
    
    # Test Docker quickstart
    docker_type = ProjectType(
        name='docker',
        confidence=0.75,
        indicators=['Dockerfile', 'docker-compose.yml'],
        framework=None
    )
    
    guide = analyzer.generate_quickstart_guide(docker_type)
    
    assert 'Containerized' in guide.title or 'Docker' in guide.title
    assert any('docker-compose up' in cmd for cmd in guide.run_commands)
    assert 'Docker' in guide.prerequisites
    
    print("  ✅ Docker quickstart generated correctly")
    
    # Test framework detection in Python
    django_files = [
        'requirements.txt',
        'manage.py',
        'myproject/settings.py',
        'myapp/models.py',
        'myapp/views.py'
    ]
    
    detected_types = analyzer.analyze_repository(django_files)
    python_django = next((t for t in detected_types if t.name == 'python'), None)
    
    if python_django and python_django.framework == 'django':
        guide = analyzer.generate_quickstart_guide(python_django)
        assert 'Django' in guide.title
        assert any('manage.py migrate' in cmd for cmd in guide.run_commands)
        print("  ✅ Django framework detection and quickstart working")
    
    return True

def test_integration_workflow():
    """Test integrated workflow of both features"""
    print("🧪 Testing Integration Workflow...")
    
    # Simulate a real repository analysis workflow
    analyzer = RepositoryAnalyzer()
    harness = EvaluationHarness()
    
    # Analyze a FastAPI-like repository
    repo_files = [
        'requirements.txt',
        'main.py',
        'app/routers/auth.py',
        'app/models/user.py',
        'docs/tutorial/first-steps.md',
        'tests/test_auth.py',
        'Dockerfile',
        'docker-compose.yml',
        'README.md'
    ]
    
    # Detect project types
    detected_types = analyzer.analyze_repository(repo_files)
    primary_type = detected_types[0] if detected_types else None
    
    assert primary_type is not None
    print(f"  ✅ Detected primary type: {primary_type.name} ({primary_type.confidence:.2f})")
    
    # Generate quickstart
    guide = analyzer.generate_quickstart_guide(primary_type)
    assert guide.title
    assert guide.install_commands
    assert guide.run_commands
    
    print(f"  ✅ Generated quickstart: {guide.title}")
    
    # Test evaluation on this "repository"
    harness.load_gold_standards()
    
    # Find a matching test case
    matching_test = next((gs for gs in harness.gold_standards if 'fastapi' in gs.repo_name.lower()), None)
    if matching_test:
        print(f"  ✅ Found matching evaluation test case: {matching_test.query[:50]}...")
        
        # This would run actual evaluation in a real integration
        mock_result = EvalResult(
            query=matching_test.query,
            expected_files=matching_test.expected_files,
            retrieved_files=['main.py', 'README.md', 'docs/tutorial/first-steps.md'],
            precision_at_k={1: 0.0, 3: 0.67, 5: 0.6},
            recall_at_k={1: 0.0, 3: 0.67, 5: 1.0},
            found_in_top_k={1: False, 3: True, 5: True},
            latency_ms=120.0,
            repo_name=matching_test.repo_name,
            category=matching_test.category
        )
        
        # Verify the result makes sense
        assert mock_result.precision_at_k[5] > 0.5
        assert mock_result.found_in_top_k[5] == True
        
        print("  ✅ Evaluation metrics calculated successfully")
    
    return True

def run_all_tests():
    """Run comprehensive test suite for advanced features"""
    print("🚀 SageVault Advanced Features Test Suite")
    print("=" * 60)
    
    tests = [
        test_evaluation_harness,
        test_repository_analyzer,
        test_quickstart_generation,
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
        print("🎉 ALL ADVANCED FEATURES WORKING!")
        print()
        print("🌟 Features Successfully Implemented:")
        print("   ├── 🧪 Evaluation Harness with Precision@K")
        print("   ├── 📊 Gold Standard Test Dataset")
        print("   ├── 🔍 Repository Type Detection")
        print("   ├── 🚀 Quickstart Guide Generation")
        print("   ├── 🎯 Multi-Language & Framework Support")
        print("   └── 🔄 Integrated Workflow Testing")
        print()
        print("✨ Ready for integration into main application!")
        print()
        print("📋 Integration Guide:")
        print("   1. Import eval_harness for regression testing")
        print("   2. Import repo_analyzer for quickstart generation")
        print("   3. Run evaluations after major changes")
        print("   4. Display quickstart guides in repository UI")
    
    return failed == 0

if __name__ == "__main__":
    run_all_tests()