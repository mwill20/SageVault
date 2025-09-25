"""
🧪 SageVault Evaluation Harness
Lightweight precision@k testing for retrieval quality validation.
Prevents regressions and measures RAG performance objectively.
"""

import json
import time
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import statistics
from datetime import datetime

@dataclass
class GoldStandardPair:
    """A gold standard query-source pair for evaluation"""
    query: str
    expected_files: List[str]  # Files that should be in top-k results
    repo_name: str
    category: str  # e.g., "setup", "api", "architecture", "bug_fix"
    difficulty: str  # "easy", "medium", "hard"
    notes: Optional[str] = None

@dataclass
class EvalResult:
    """Results for a single evaluation query"""
    query: str
    expected_files: List[str]
    retrieved_files: List[str]
    precision_at_k: Dict[int, float]  # k -> precision score
    recall_at_k: Dict[int, float]
    found_in_top_k: Dict[int, bool]
    latency_ms: float
    repo_name: str
    category: str

class EvaluationHarness:
    """
    Lightweight evaluation system for RAG retrieval quality.
    Measures precision@k to prevent regressions after changes.
    """
    
    def __init__(self, rag_system=None):
        """Initialize with RAG system instance"""
        self.rag_system = rag_system
        self.gold_standards = []
        self.results_history = []
    
    def load_gold_standards(self, dataset_path: str = None):
        """Load gold standard Q→source pairs"""
        if dataset_path and Path(dataset_path).exists():
            with open(dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.gold_standards = [GoldStandardPair(**item) for item in data]
        else:
            # Use built-in gold standards
            self.gold_standards = self._create_builtin_gold_standards()
    
    def _create_builtin_gold_standards(self) -> List[GoldStandardPair]:
        """Create built-in gold standard test cases for popular repos"""
        return [
            # FastAPI repository tests
            GoldStandardPair(
                query="How do I create a basic FastAPI application?",
                expected_files=["fastapi/applications.py", "docs/tutorial/first-steps.md", "README.md"],
                repo_name="tiangolo/fastapi",
                category="quickstart",
                difficulty="easy",
                notes="Basic setup question should find main app file and tutorial"
            ),
            GoldStandardPair(
                query="How do I add authentication middleware?",
                expected_files=["fastapi/security/__init__.py", "fastapi/security/oauth2.py", "docs/tutorial/security/"],
                repo_name="tiangolo/fastapi",
                category="security",
                difficulty="medium",
                notes="Security-related files should be top results"
            ),
            GoldStandardPair(
                query="How do I handle database connections?",
                expected_files=["docs/tutorial/sql-databases.md", "docs/tutorial/dependencies/"],
                repo_name="tiangolo/fastapi",
                category="database",
                difficulty="medium",
                notes="Database documentation should rank highly"
            ),
            
            # Streamlit repository tests
            GoldStandardPair(
                query="How do I create a simple Streamlit app?",
                expected_files=["README.md", "docs/get-started.md", "streamlit/hello.py"],
                repo_name="streamlit/streamlit",
                category="quickstart",
                difficulty="easy",
                notes="Basic app creation should find main docs and examples"
            ),
            GoldStandardPair(
                query="How do I add widgets to my app?",
                expected_files=["streamlit/elements/", "docs/api-reference.md", "streamlit/elements/widgets/"],
                repo_name="streamlit/streamlit",
                category="widgets",
                difficulty="easy",
                notes="Widget documentation and implementation files"
            ),
            GoldStandardPair(
                query="How do I handle session state?",
                expected_files=["streamlit/session_state.py", "docs/session-state.md"],
                repo_name="streamlit/streamlit",
                category="state_management",
                difficulty="medium",
                notes="Session state implementation and docs"
            ),
            
            # Requests repository tests  
            GoldStandardPair(
                query="How do I make a GET request?",
                expected_files=["README.md", "docs/user/quickstart.rst", "requests/api.py"],
                repo_name="psf/requests",
                category="quickstart", 
                difficulty="easy",
                notes="Basic usage should find main docs and API"
            ),
            GoldStandardPair(
                query="How do I handle authentication?",
                expected_files=["requests/auth.py", "docs/user/authentication.rst"],
                repo_name="psf/requests",
                category="auth",
                difficulty="medium",
                notes="Authentication implementation and documentation"
            ),
            GoldStandardPair(
                query="How do I configure SSL certificates?",
                expected_files=["requests/adapters.py", "docs/user/advanced.rst", "requests/packages/urllib3/"],
                repo_name="psf/requests",
                category="ssl",
                difficulty="hard",
                notes="Advanced SSL configuration files"
            ),
        ]
    
    def run_evaluation(self, k_values: List[int] = [1, 3, 5, 10], repo_filter: str = None) -> Dict[str, Any]:
        """Run evaluation on all gold standards"""
        if not self.rag_system:
            raise ValueError("RAG system not provided. Cannot run evaluation.")
        
        results = []
        test_cases = self.gold_standards
        
        if repo_filter:
            test_cases = [gs for gs in test_cases if repo_filter in gs.repo_name]
        
        print(f"🧪 Running evaluation on {len(test_cases)} test cases...")
        print(f"📊 Measuring precision@k for k = {k_values}")
        
        for i, gold_standard in enumerate(test_cases, 1):
            print(f"  [{i}/{len(test_cases)}] Testing: {gold_standard.query[:50]}...")
            
            # Measure retrieval latency
            start_time = time.time()
            
            try:
                # Retrieve documents using RAG system
                retrieved_docs = self._retrieve_documents(gold_standard.query, gold_standard.repo_name)
                latency_ms = (time.time() - start_time) * 1000
                
                # Calculate metrics
                result = self._calculate_metrics(gold_standard, retrieved_docs, k_values, latency_ms)
                results.append(result)
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
                continue
        
        # Aggregate results
        summary = self._aggregate_results(results, k_values)
        
        # Store results
        self.results_history.append({
            'timestamp': datetime.now().isoformat(),
            'summary': summary,
            'individual_results': results
        })
        
        return summary
    
    def _retrieve_documents(self, query: str, repo_name: str) -> List[Dict[str, Any]]:
        """Retrieve documents using the RAG system"""
        # This would interface with your actual RAG system
        # For now, return mock results that would come from vector search
        
        # Mock implementation - replace with actual RAG system call
        mock_results = [
            {'filename': 'README.md', 'similarity_score': 0.95, 'content': 'Mock content'},
            {'filename': 'docs/tutorial.md', 'similarity_score': 0.88, 'content': 'Mock content'},
            {'filename': 'src/main.py', 'similarity_score': 0.82, 'content': 'Mock content'},
            {'filename': 'tests/test_main.py', 'similarity_score': 0.75, 'content': 'Mock content'},
            {'filename': 'setup.py', 'similarity_score': 0.68, 'content': 'Mock content'},
        ]
        
        return mock_results
    
    def _calculate_metrics(self, gold_standard: GoldStandardPair, retrieved_docs: List[Dict], 
                          k_values: List[int], latency_ms: float) -> EvalResult:
        """Calculate precision@k and recall@k metrics"""
        
        retrieved_files = [doc['filename'] for doc in retrieved_docs]
        expected_files = gold_standard.expected_files
        
        precision_at_k = {}
        recall_at_k = {}
        found_in_top_k = {}
        
        for k in k_values:
            top_k_files = retrieved_files[:k]
            
            # Calculate precision@k
            relevant_in_top_k = sum(1 for f in top_k_files if any(exp in f for exp in expected_files))
            precision_at_k[k] = relevant_in_top_k / k if k > 0 else 0
            
            # Calculate recall@k  
            total_relevant_found = sum(1 for exp in expected_files if any(exp in f for f in top_k_files))
            recall_at_k[k] = total_relevant_found / len(expected_files) if expected_files else 0
            
            # Check if any expected file found in top-k
            found_in_top_k[k] = any(any(exp in f for f in top_k_files) for exp in expected_files)
        
        return EvalResult(
            query=gold_standard.query,
            expected_files=expected_files,
            retrieved_files=retrieved_files,
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            found_in_top_k=found_in_top_k,
            latency_ms=latency_ms,
            repo_name=gold_standard.repo_name,
            category=gold_standard.category
        )
    
    def _aggregate_results(self, results: List[EvalResult], k_values: List[int]) -> Dict[str, Any]:
        """Aggregate individual results into summary statistics"""
        
        if not results:
            return {"error": "No results to aggregate"}
        
        summary = {
            'total_queries': len(results),
            'avg_latency_ms': statistics.mean([r.latency_ms for r in results]),
            'metrics_by_k': {},
            'metrics_by_category': {},
            'overall_performance': {}
        }
        
        # Aggregate by k value
        for k in k_values:
            precisions = [r.precision_at_k[k] for r in results]
            recalls = [r.recall_at_k[k] for r in results]
            hit_rate = sum(1 for r in results if r.found_in_top_k[k]) / len(results)
            
            summary['metrics_by_k'][f'precision@{k}'] = {
                'mean': statistics.mean(precisions),
                'min': min(precisions),
                'max': max(precisions),
                'std': statistics.stdev(precisions) if len(precisions) > 1 else 0
            }
            
            summary['metrics_by_k'][f'recall@{k}'] = {
                'mean': statistics.mean(recalls),
                'min': min(recalls), 
                'max': max(recalls),
                'std': statistics.stdev(recalls) if len(recalls) > 1 else 0
            }
            
            summary['metrics_by_k'][f'hit_rate@{k}'] = hit_rate
        
        # Aggregate by category
        categories = set(r.category for r in results)
        for category in categories:
            cat_results = [r for r in results if r.category == category]
            if cat_results:
                summary['metrics_by_category'][category] = {
                    'count': len(cat_results),
                    'avg_precision@5': statistics.mean([r.precision_at_k.get(5, 0) for r in cat_results]),
                    'hit_rate@5': sum(1 for r in cat_results if r.found_in_top_k.get(5, False)) / len(cat_results)
                }
        
        # Overall performance grade
        avg_precision_5 = summary['metrics_by_k'].get('precision@5', {}).get('mean', 0)
        avg_hit_rate_5 = summary['metrics_by_k'].get('hit_rate@5', 0)
        
        if avg_precision_5 >= 0.8 and avg_hit_rate_5 >= 0.9:
            grade = "🟢 Excellent"
        elif avg_precision_5 >= 0.6 and avg_hit_rate_5 >= 0.8:
            grade = "🟡 Good"
        elif avg_precision_5 >= 0.4 and avg_hit_rate_5 >= 0.6:
            grade = "🟠 Fair"
        else:
            grade = "🔴 Needs Improvement"
        
        summary['overall_performance'] = {
            'grade': grade,
            'precision@5': avg_precision_5,
            'hit_rate@5': avg_hit_rate_5
        }
        
        return summary
    
    def print_results(self, summary: Dict[str, Any]):
        """Print formatted evaluation results"""
        print("\n" + "="*60)
        print("🧪 SAGEVAULT EVALUATION RESULTS")
        print("="*60)
        
        # Overall performance
        perf = summary['overall_performance']
        print(f"\n🎯 Overall Performance: {perf['grade']}")
        print(f"   Precision@5: {perf['precision@5']:.3f}")
        print(f"   Hit Rate@5: {perf['hit_rate@5']:.3f}")
        print(f"   Avg Latency: {summary['avg_latency_ms']:.1f}ms")
        
        # Metrics by k
        print(f"\n📊 Precision@K Metrics:")
        for k in [1, 3, 5, 10]:
            if f'precision@{k}' in summary['metrics_by_k']:
                p_stats = summary['metrics_by_k'][f'precision@{k}']
                hit_rate = summary['metrics_by_k'].get(f'hit_rate@{k}', 0)
                print(f"   P@{k}: {p_stats['mean']:.3f} ± {p_stats['std']:.3f} | Hit Rate: {hit_rate:.3f}")
        
        # Category breakdown
        print(f"\n🏷️  Performance by Category:")
        for category, stats in summary['metrics_by_category'].items():
            print(f"   {category}: P@5={stats['avg_precision@5']:.3f}, Hit@5={stats['hit_rate@5']:.3f} ({stats['count']} queries)")
        
        print("\n" + "="*60)
    
    def save_results(self, filepath: str = None):
        """Save evaluation results to file"""
        if not filepath:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"eval_results_{timestamp}.json"
        
        # Convert dataclass objects to dictionaries for JSON serialization
        serializable_history = []
        for history_item in self.results_history:
            serializable_item = {
                'timestamp': history_item['timestamp'],
                'summary': history_item['summary'],
                'individual_results': []
            }
            
            for result in history_item['individual_results']:
                if hasattr(result, '__dict__'):
                    # Convert dataclass to dict
                    result_dict = {
                        'query': result.query,
                        'expected_files': result.expected_files,
                        'retrieved_files': result.retrieved_files,
                        'precision_at_k': result.precision_at_k,
                        'recall_at_k': result.recall_at_k,
                        'found_in_top_k': result.found_in_top_k,
                        'latency_ms': result.latency_ms,
                        'repo_name': result.repo_name,
                        'category': result.category
                    }
                    serializable_item['individual_results'].append(result_dict)
                else:
                    serializable_item['individual_results'].append(result)
            
            serializable_history.append(serializable_item)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_history, f, indent=2, ensure_ascii=False)
        
        print(f"📁 Results saved to: {filepath}")
        return filepath
    
    def regression_test(self, baseline_results: Dict[str, Any], tolerance: float = 0.05) -> bool:
        """Compare current results against baseline to detect regressions"""
        if not self.results_history:
            print("❌ No current results to compare")
            return False
        
        current = self.results_history[-1]['summary']
        
        # Compare key metrics
        current_p5 = current['overall_performance']['precision@5']
        baseline_p5 = baseline_results['overall_performance']['precision@5']
        
        current_hr5 = current['overall_performance']['hit_rate@5']
        baseline_hr5 = baseline_results['overall_performance']['hit_rate@5']
        
        p5_regression = (baseline_p5 - current_p5) > tolerance
        hr5_regression = (baseline_hr5 - current_hr5) > tolerance
        
        if p5_regression or hr5_regression:
            print("🚨 REGRESSION DETECTED!")
            print(f"  Precision@5: {baseline_p5:.3f} → {current_p5:.3f} (Δ{current_p5-baseline_p5:+.3f})")
            print(f"  Hit Rate@5: {baseline_hr5:.3f} → {current_hr5:.3f} (Δ{current_hr5-baseline_hr5:+.3f})")
            return False
        else:
            print("✅ No regression detected - performance maintained")
            return True

# Global evaluation instance
eval_harness = EvaluationHarness()

# Example usage:
"""
# Initialize with RAG system
eval_harness = EvaluationHarness(rag_system=your_rag_instance)

# Load gold standards
eval_harness.load_gold_standards("path/to/gold_standards.json")

# Run evaluation
results = eval_harness.run_evaluation(k_values=[1, 3, 5, 10])

# Print results
eval_harness.print_results(results)

# Save for baseline comparison
eval_harness.save_results("baseline_results.json")

# Later, check for regressions
eval_harness.regression_test(baseline_results)
"""