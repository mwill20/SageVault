"""Simple test app to verify Streamlit UI works"""
import streamlit as st

st.set_page_config(page_title="Test App", layout="wide")

st.title("🧪 UI Test App")
st.write("Testing if buttons and inputs work...")

# Test input
test_url = st.text_input("Test URL Input", placeholder="Enter something here...")

# Test button in columns
col1, col2 = st.columns([2, 1])

with col1:
    st.write("Column 1 content")

with col2:
    test_button = st.button("🔍 Test Button", type="primary", use_container_width=True)

if test_button:
    st.success("✅ Button clicked!")
    if test_url:
        st.write(f"URL entered: {test_url}")
    else:
        st.write("No URL entered")

# Test text area and another button
st.markdown("---")
question = st.text_area("Test Question", placeholder="Ask something...")
answer_button = st.button("Get Test Answer", type="primary")

if answer_button and question:
    st.write(f"You asked: {question}")

st.info("If you can see this and the buttons work, the basic UI is functioning!")