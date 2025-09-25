# 🧪 Advanced Features Integration Guide

This document provides implementation guidance for integrating the newly developed advanced features into the main SageVault application.

## ✅ **Features Completed**

### 1. **🧪 Lightweight Evaluation Harness**
- **File**: `eval_harness.py`
- **Purpose**: Precision@K testing with gold standard Q→source pairs
- **Output**: Prevents regressions, measures RAG quality objectively

### 2. **🔍 Repository Type Detection & Quickstarts**
- **File**: `repo_analyzer.py`
- **Purpose**: Auto-detect project types and generate tailored getting started guides
- **Output**: Professional quickstart guides without code execution

## 🔧 **Integration Steps**

### Step 1: Import the New Modules

Add to `streamlit_app_clean.py`:

```python
from eval_harness import eval_harness, EvaluationHarness
from repo_analyzer import repo_analyzer, RepositoryAnalyzer
```

### Step 2: Add Repository Analysis After Indexing

After successful repository indexing:

```python
def handle_repository_indexing(repo_url: str, file_list: List[str]):
    # ... existing indexing code ...
    
    # After successful indexing, analyze repository type
    analyzer = RepositoryAnalyzer()
    detected_types = analyzer.analyze_repository(file_list)
    
    if detected_types:
        primary_type = detected_types[0]  # Highest confidence
        quickstart_guide = analyzer.generate_quickstart_guide(primary_type)
        
        # Store in session state for UI display
        st.session_state['detected_project_type'] = primary_type
        st.session_state['quickstart_guide'] = quickstart_guide
        
        # Show success message with detected type
        st.success(f"✅ Repository indexed! Detected: {primary_type.name.title()} project")
        if primary_type.framework:
            st.info(f"🔍 Framework detected: {primary_type.framework.title()}")
```

### Step 3: Display Quickstart Guide in UI

Add quickstart display section:

```python
# After repository indexing success
if 'quickstart_guide' in st.session_state:
    guide = st.session_state['quickstart_guide']
    
    with st.expander(f"🚀 Getting Started with {guide.title}", expanded=True):
        st.markdown(f"**{guide.description}**")
        
        # Prerequisites
        if guide.prerequisites:
            st.markdown("**Prerequisites:**")
            for prereq in guide.prerequisites:
                st.markdown(f"- {prereq}")
        
        # Installation commands
        if guide.install_commands:
            st.markdown("**Installation:**")
            install_code = '\n'.join(guide.install_commands)
            st.code(install_code, language='bash')
        
        # Run commands
        if guide.run_commands:
            st.markdown("**Run:**")
            run_code = '\n'.join(guide.run_commands)
            st.code(run_code, language='bash')
        
        # Additional notes
        if guide.additional_notes:
            st.markdown("**Additional Notes:**")
            for note in guide.additional_notes:
                st.markdown(f"- {note}")
        
        # Links
        if guide.links:
            st.markdown("**Useful Links:**")
            for link in guide.links:
                st.markdown(f"- [{link['text']}]({link['url']})")
```

### Step 4: Add Evaluation Testing (Development/Admin)

Add evaluation controls for development:

```python
# In sidebar or admin section
if st.sidebar.checkbox("🧪 Developer Mode"):
    st.sidebar.markdown("### Evaluation Harness")
    
    if st.sidebar.button("Run RAG Evaluation"):
        with st.spinner("Running precision@K evaluation..."):
            # Initialize evaluation harness with current RAG system
            harness = EvaluationHarness(rag_system=your_rag_instance)
            harness.load_gold_standards()
            
            # Run evaluation
            results = harness.run_evaluation(k_values=[1, 3, 5, 10])
            
            # Display results
            st.markdown("## 🧪 Evaluation Results")
            
            # Performance grade
            perf = results['overall_performance']
            st.metric("Overall Performance", perf['grade'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Precision@5", f"{perf['precision@5']:.3f}")
            with col2:
                st.metric("Hit Rate@5", f"{perf['hit_rate@5']:.3f}")
            
            # Detailed metrics
            with st.expander("📊 Detailed Metrics"):
                st.json(results)
            
            # Save results for regression testing
            filename = harness.save_results()
            st.success(f"Results saved to: {filename}")
```

### Step 5: Repository Type Display in Sidebar

Add repository info to sidebar:

```python
# In sidebar after successful indexing
if 'detected_project_type' in st.session_state:
    project_type = st.session_state['detected_project_type']
    
    st.sidebar.markdown("### 📋 Repository Info")
    st.sidebar.metric("Project Type", project_type.name.title())
    
    if project_type.framework:
        st.sidebar.metric("Framework", project_type.framework.title())
    
    st.sidebar.metric("Detection Confidence", f"{project_type.confidence:.0%}")
    
    # Show detection indicators
    with st.sidebar.expander("🔍 Detection Details"):
        st.write("**Indicators found:**")
        for indicator in project_type.indicators[:5]:  # Show top 5
            st.write(f"- `{indicator}`")
```

## 🎨 **UI Enhancement Examples**

### Enhanced Repository Status Display

```python
def show_repository_status():
    if 'quickstart_guide' in st.session_state:
        guide = st.session_state['quickstart_guide']
        project_type = st.session_state['detected_project_type']
        
        # Create status card
        st.markdown(f"""
        <div style="padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #1f77b4;">
            <h4>🎯 {guide.title}</h4>
            <p>{guide.description}</p>
            <p><strong>Confidence:</strong> {project_type.confidence:.0%}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Show Setup Guide"):
                st.session_state['show_quickstart'] = True
        
        with col2:
            if st.button("🧪 Run Evaluation"):
                st.session_state['run_evaluation'] = True
        
        with col3:
            if st.button("🔄 Re-analyze"):
                # Trigger re-analysis
                pass
```

### Evaluation Dashboard Widget

```python
def show_evaluation_dashboard():
    st.markdown("### 🧪 Quality Metrics")
    
    # Mock current performance (replace with real data)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Precision@5", "0.85", "0.05")
    with col2:
        st.metric("Hit Rate@5", "0.92", "0.02")
    with col3:
        st.metric("Avg Latency", "1.2s", "-0.1s")
    with col4:
        st.metric("Total Tests", "27", "3")
    
    # Trend chart (if historical data available)
    if st.checkbox("📈 Show Trends"):
        st.line_chart({"Precision@5": [0.80, 0.82, 0.85], "Hit Rate@5": [0.90, 0.91, 0.92]})
```

## 🧪 **Testing Integration**

### Running Evaluations

```bash
# Run evaluation harness standalone
python eval_harness.py

# Run repository analyzer standalone  
python repo_analyzer.py

# Run comprehensive tests
python test_advanced_features.py
```

### Expected Outputs

**Evaluation Results:**
```
🎯 Overall Performance: 🟢 Excellent
   Precision@5: 0.850
   Hit Rate@5: 0.920
   Avg Latency: 120.5ms

📊 Precision@K Metrics:
   P@1: 0.650 ± 0.150 | Hit Rate: 0.650
   P@3: 0.750 ± 0.120 | Hit Rate: 0.850
   P@5: 0.850 ± 0.100 | Hit Rate: 0.920
```

**Repository Analysis:**
```
🔍 Detected: Python (Streamlit) Project
📋 Installation: pip install -r requirements.txt
🚀 Run: streamlit run app.py
🎯 Confidence: 85%
```

## 🔒 **Quality Assurance**

### Regression Testing

Set up automated regression testing:

```python
def run_regression_test():
    """Run regression test against baseline"""
    harness = EvaluationHarness(rag_system=current_system)
    
    # Load baseline results
    with open('baseline_results.json', 'r') as f:
        baseline = json.load(f)
    
    # Run current evaluation
    current_results = harness.run_evaluation()
    
    # Check for regressions
    if harness.regression_test(baseline['summary'], tolerance=0.05):
        print("✅ No regression detected")
        return True
    else:
        print("🚨 Performance regression detected!")
        return False
```

### Monitoring

```python
# Add to your monitoring/logging
def log_evaluation_metrics(results):
    """Log evaluation metrics for monitoring"""
    metrics = {
        'precision_at_5': results['overall_performance']['precision@5'],
        'hit_rate_at_5': results['overall_performance']['hit_rate@5'],
        'avg_latency': results['avg_latency_ms'],
        'timestamp': datetime.now().isoformat()
    }
    
    # Log to your monitoring system
    logger.info("Evaluation metrics", extra=metrics)
```

## 🚀 **Production Deployment**

1. **Enable evaluation harness in development/staging**
2. **Set up baseline measurements**
3. **Integrate repository type detection in production**
4. **Add quickstart guides to user experience**
5. **Monitor precision@K metrics over time**

## 📊 **Expected Impact**

### User Experience
- **Immediate value**: Users see project type and setup instructions
- **Reduced friction**: No guessing about how to run/install
- **Professional polish**: Shows SageVault understands their codebase

### Quality Assurance  
- **Regression prevention**: Catch quality drops before users do
- **Objective measurement**: Data-driven quality decisions
- **Continuous improvement**: Track improvements over time

---
*Integration guide complete - all advanced features ready for production use!* ✨