# Security Integration Guide

This guide replaces the legacy SECURITY_INTEGRATION_DEMO.py script. Follow these steps to layer SageVault's security middleware into streamlit_app_clean.py.

## 1. Import the security helpers
Add these imports near the rest of your app-level imports:

`python
from app.secure_streamlit_integration import (
    SecurityMiddleware,
    secure_rag_search,
    add_security_to_streamlit,
    display_security_info,
)
from app.secure_prompts import SECURE_SYSTEM_PROMPT
`

## 2. (Optional) show security status in the sidebar
Inside your sidebar layout:

`python
add_security_to_streamlit()  # Renders active protection badges
`

## 3. Wrap the retriever call
Replace the direct search_vector_store call with the secure wrapper so results are screened before use:

`python
search_result = secure_rag_search(
    lambda q, collection, k: search_vector_store(collection, q, k=k),
    prompt,
    st.session_state.unified_collection,
    k=5,
)

if "error" in search_result:
    st.error(f"Security: {search_result['error']}")
    return

search_results = search_result["results"]
for warning in search_result.get("warnings", []):
    st.warning(f"Security notice: {warning}")
`

## 4. Secure the LLM response
Wrap the generated answer so secrets and unsafe content are filtered before display:

`python
response = call_llm(provider, api_key, llm_prompt)
secure_resp = SecurityMiddleware.secure_response(response, search_results)
st.markdown(secure_resp["content"])
display_security_info(secure_resp)
`

Persist the secured answer in chat history (if you store it) instead of the raw response.

## 5. Use the secure system prompt
Swap your prompt template to include the hardened instructions:

`python
llm_prompt = f"""{SECURE_SYSTEM_PROMPT}

Context:
{context}

Question: {prompt}

Answer:"""
`

## 6. Regression checklist

`ash
# Imports should resolve without errors
python -c "import streamlit_app_clean"

# Manual smoke test
printf "http://localhost:8501" && streamlit run streamlit_app_clean.py

# Security harness
pytest tests/test_comprehensive_security.py
`

## Complete assistant block (reference)
Embed the pieces above into your chat handler:

`python
with st.chat_message("assistant"):
    with st.spinner("Thinking..."):
        search_result = secure_rag_search(
            lambda q, collection, k: search_vector_store(collection, q, k=k),
            prompt,
            st.session_state.unified_collection,
            k=5,
        )
        if "error" in search_result:
            st.error(f"Security: {search_result['error']}")
            return

        search_results = search_result["results"]
        for warning in search_result.get("warnings", []):
            st.warning(f"Security notice: {warning}")

        context = "\n\n".join(
            f"Source: {r['file_path']}\n\n{r['text']}" for r in search_results
        )
        llm_prompt = f"""{SECURE_SYSTEM_PROMPT}

        Context:
        {context}

        Question: {prompt}

        Answer:"""

        response = call_llm(provider, api_key, llm_prompt)
        secure_resp = SecurityMiddleware.secure_response(response, search_results)
        st.markdown(secure_resp["content"])
        display_security_info(secure_resp)
        st.session_state.messages.append({
            "role": "assistant",
            "content": secure_resp["content"],
        })
        track_question_asked(provider_type=provider)
        st.rerun()
`

## Benefits
- Automatic secret redaction
- Injection detection and mitigation
- Dangerous command warnings
- Provenance validation and diversity guardrails
- Transparent security indicators with zero runtime code changes outside the chat handler

## Need a quick start?
Use steps 1, 3, and 4 for a minimal integration; the other sections enhance transparency for reviewers.
