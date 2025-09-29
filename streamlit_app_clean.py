"""SageVault - A Conversational UI for RAG"""
import streamlit as st
import requests
from urllib.parse import urlparse
from typing import Dict, List, Tuple
import os
import sys
import io
import pandas as pd

# Import utilities
from simple_rag import create_or_update_unified_vector_store, add_to_vector_store, search_vector_store
from analytics import track_index_built, track_question_asked, track_files_processed, track_security_override, track_document_upload, get_session_summary, clear_analytics
from utilities.repo_analyzer import repo_analyzer

# Security integration (automatic protection)
from app.security.secure_streamlit_integration import SecurityMiddleware, secure_rag_search, display_security_info
from app.security.secure_prompts import SECURE_SYSTEM_PROMPT

# --- Utility Functions from the original file ---

def extract_text_from_pdf(file_bytes: bytes) -> str:
    # This function remains the same
    # (Implementation is omitted for brevity but is included in the final code)
    pass

def extract_text_from_docx(file_bytes: bytes) -> str:
    # This function remains the same
    # (Implementation is omitted for brevity but is included in the final code)
    pass

def extract_text_from_file(uploaded_file) -> Tuple[str, str]:
    # This function remains the same
    # (Implementation is omitted for brevity but is included in the final code)
    pass

def parse_github_url(url: str) -> Tuple[str, str]:
    # This function remains the same
    # (Implementation is omitted for brevity but is included in the final code)
    pass

def fetch_github_files(owner: str, repo: str, max_files: int = 100, github_token: str = None) -> tuple[Dict[str, str], List[Dict]]:
    # This function remains the same
    # (Implementation is omitted for brevity but is included in the final code)
    pass

def call_llm(provider: str, api_key: str, prompt: str) -> str:
    # This function remains the same
    # (Implementation is omitted for brevity but is included in the final code)
    pass

# --- Full implementations of utility functions ---

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF file using multiple methods"""
    text = ""
    try:
        import PyPDF2
        pdf_file = io.BytesIO(file_bytes)
        reader = PyPDF2.PdfReader(pdf_file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
        if len(text.strip()) > 100:
            return text.strip()
    except Exception as e:
        print(f"PyPDF2 failed: {e}")

    try:
        import pdfplumber
        pdf_file = io.BytesIO(file_bytes)
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
        if text.strip():
            return text.strip()
    except Exception as e:
        print(f"pdfplumber failed: {e}")
        return f"Error processing PDF: {e}"
        
    return "Could not extract text from PDF. It may be image-based."

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX file"""
    try:
        from docx import Document
        doc_file = io.BytesIO(file_bytes)
        doc = Document(doc_file)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        return f"Error processing DOCX: {e}"

def extract_text_from_file(uploaded_file) -> Tuple[str, str]:
    """Extract text from uploaded file based on file type"""
    file_extension = uploaded_file.name.lower().split('.')[-1]
    file_bytes = uploaded_file.read()
    
    if file_extension == 'pdf':
        text = extract_text_from_pdf(file_bytes)
    elif file_extension == 'docx':
        text = extract_text_from_docx(file_bytes)
    else: # Assume text-based
        try:
            text = file_bytes.decode('utf-8', errors='ignore')
        except Exception as e:
            text = f"Error decoding file: {e}"
            
    return uploaded_file.name, text

def parse_github_url(url: str) -> Tuple[str, str]:
    """Extract owner and repo from GitHub URL"""
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split('/') if p]
    if len(parts) < 2:
        raise ValueError("URL must be in format: https://github.com/owner/repo")
    return parts[0], parts[1]

def fetch_github_files(owner: str, repo: str, max_files: int = 100, github_token: str = None) -> tuple[Dict[str, str], List[Dict]]:
    """Fetch text files from GitHub repository"""
    files = {}
    excluded_files = []
    headers = {'Authorization': f'token {github_token}'} if github_token else {}
    
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
    response = requests.get(tree_url, headers=headers, timeout=30)
    if response.status_code != 200:
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1"
        response = requests.get(tree_url, headers=headers, timeout=30)
    
    if response.status_code != 200:
        raise Exception(f"GitHub API error ({response.status_code}): Could not fetch repository tree.")

    tree_data = response.json().get('tree', [])
    
    text_extensions = {'.md', '.txt', '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.html', '.css', '.json', '.yml', '.yaml', '.sh'}
    
    count = 0
    for item in tree_data:
        if item['type'] == 'blob' and any(item['path'].endswith(ext) for ext in text_extensions) and count < max_files:
            try:
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{item['path']}"
                file_response = requests.get(raw_url, headers=headers, timeout=15)
                if file_response.status_code != 200:
                    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{item['path']}"
                    file_response = requests.get(raw_url, headers=headers, timeout=15)
                
                if file_response.status_code == 200 and len(file_response.content) < 100000:
                    content = file_response.content.decode('utf-8', errors='ignore')
                    if content.strip():
                        files[item['path']] = content
                        count += 1
                else:
                    excluded_files.append({'file_path': item['path'], 'reason': f'Skipped (large or inaccessible)'})
            except Exception as e:
                excluded_files.append({'file_path': item['path'], 'reason': f'Error: {e}'})
        elif item['type'] == 'blob':
             excluded_files.append({'file_path': item['path'], 'reason': 'Skipped (non-text file)'})

    return files, excluded_files

def call_llm(provider: str, api_key: str, prompt: str) -> str:
    """Call LLM with the given prompt"""
    if not api_key or provider == "None":
        return "Please select an LLM provider and provide an API key in the sidebar."
    
    try:
        if provider == "Groq":
            from groq import Groq
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}], temperature=0.2, max_tokens=1024)
            return response.choices[0].message.content
        elif provider == "OpenAI":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.2, max_tokens=1024)
            return response.choices[0].message.content
        elif provider == "Anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(model="claude-3-5-sonnet-20240620", messages=[{"role": "user", "content": prompt}], temperature=0.2, max_tokens=1024)
            return response.content[0].text
        elif provider == "Google":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(max_output_tokens=1024, temperature=0.2))
            return response.text
    except Exception as e:
        return f"API Error: {e}"
    return "Unknown provider."


# --- Streamlit App ---

st.set_page_config(page_title="SageVault", layout="wide", page_icon="🔍", initial_sidebar_state="expanded")

# --- Session State Initialization ---
if 'unified_collection' not in st.session_state:
    st.session_state.unified_collection = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'sources' not in st.session_state:
    st.session_state.sources = []
if 'indexed_files_count' not in st.session_state:
    st.session_state.indexed_files_count = 0
if 'excluded_files' not in st.session_state:
    st.session_state.excluded_files = []
if 'indexed_files' not in st.session_state:
    st.session_state.indexed_files = []
if 'repo_url' not in st.session_state:
    st.session_state.repo_url = ""

# --- Sidebar for Settings ---
with st.sidebar:
    st.markdown("# 📖 **<span style='color: #1f77b4;'>How to use:</span>**", unsafe_allow_html=True)
    st.markdown("**<span style='color: #1f77b4;'>1.</span> Add a GitHub repo and/or upload documents.**\n\n**<span style='color: #1f77b4;'>2.</span> Click 'Index All'.**\n\n**<span style='color: #1f77b4;'>3.</span> Ask questions in the chat window.**", unsafe_allow_html=True)
    st.markdown("---")
    st.header("⚙️ Settings")
    provider = st.selectbox("LLM Provider", ["None", "Groq", "OpenAI", "Anthropic", "Google"])
    api_key = st.text_input("API Key", type="password", help="Your API key (stored only for this session)")
    st.markdown("---")
    st.subheader("🔑 GitHub Token (Optional)")
    github_token = st.text_input("GitHub Personal Access Token", type="password", help="Increases API rate limits for public repos")
    st.markdown("---")
    st.subheader("🔧 RAG Settings")
    chunk_size = st.slider("Chunk Size", 200, 1500, 500, 50, help="Size of text chunks for processing.")
    overlap_percent = st.slider("Chunk Overlap (%)", 0, 50, 10, 5, help="Percentage overlap between chunks.")
    st.markdown("---")
    st.subheader("🔒 Security Status")
    st.success("✅ Injection Protection: Active")
    st.success("✅ Secret Redaction: Active") 
    st.success("✅ Command Safety: Active")
    st.info("🛡️ System automatically protected")

# --- Main App Layout ---
# Logo positioned on the left where title was with blue highlight
try:
    # Add custom CSS for image highlighting
    st.markdown("""
    <style>
    .logo-container img {
        border: 3px solid #1f77b4 !important;
        border-radius: 15px !important;
        padding: 15px !important;
        background: linear-gradient(135deg, rgba(31, 119, 180, 0.1), rgba(31, 119, 180, 0.05)) !important;
        box-shadow: 0 4px 12px rgba(31, 119, 180, 0.3) !important;
        margin-bottom: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Use container with custom class
    with st.container():
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        st.image("assets/sagevault-logo.png", width=400)  # Large logo on the left
        st.markdown('</div>', unsafe_allow_html=True)
except:
    st.title("🔍 SageVault")  # Fallback if logo fails

left_column, right_column = st.columns([1, 1.5])

# --- Left Column: Data Sources & Controls ---
with left_column:
    st.subheader("Add Data Sources")
    repo_url_input = st.text_input("Add GitHub Repo URL", placeholder="https://github.com/owner/repository", value=st.session_state.repo_url)
    uploaded_files = st.file_uploader("Download Docs", accept_multiple_files=True, type=['pdf', 'docx', 'txt', 'md', 'py', 'js', 'html', 'css', 'json', 'yml', 'yaml'])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Index All", type="primary"):
            st.session_state.repo_url = repo_url_input
            with st.spinner("Indexing all sources... Please wait."):
                # Clear previous index
                st.session_state.unified_collection = None
                st.session_state.messages = []
                st.session_state.sources = []
                st.session_state.indexed_files_count = 0
                st.session_state.excluded_files = []
                st.session_state.indexed_files = []

                all_docs = {}
                
                # 1. Process GitHub Repository
                if st.session_state.repo_url:
                    try:
                        owner, repo = parse_github_url(st.session_state.repo_url)
                        repo_files, excluded_repo = fetch_github_files(owner, repo, github_token=github_token)
                        all_docs.update(repo_files)
                        st.session_state.excluded_files.extend(excluded_repo)
                        st.success(f"Fetched {len(repo_files)} files from repository.")
                    except Exception as e:
                        st.error(f"Repo Error: {e}")

                # 2. Process Uploaded Documents
                if uploaded_files:
                    try:
                        for uploaded_file in uploaded_files:
                            filename, text = extract_text_from_file(uploaded_file)
                            if text and not text.startswith("Error"):
                                # Automatic security: redact any secrets in uploaded documents
                                from app.security.security_utils import redact_secrets
                                secure_text = redact_secrets(text)
                                all_docs[f"uploaded:{filename}"] = secure_text
                                
                                # Log if secrets were redacted
                                if "[REDACTED]" in secure_text:
                                    st.info(f"🔒 Security: Redacted potential secrets from {filename}")
                            else:
                                st.session_state.excluded_files.append({'file_path': filename, 'reason': 'Failed to extract text'})
                        st.success(f"Processed {len(uploaded_files)} uploaded documents.")
                    except Exception as e:
                        st.error(f"Upload Error: {e}")

                # 3. Create unified vector store

                if all_docs:
                    try:
                        st.session_state.unified_collection = create_or_update_unified_vector_store("unified_sagevault")
                        # Pass repo name for dynamic source tagging
                        repo_name = "Repository"
                        if st.session_state.repo_url:
                            try:
                                owner, repo = parse_github_url(st.session_state.repo_url)
                                repo_name = repo
                            except Exception:
                                repo_name = "Repository"
                        metadata = {"repo_name": repo_name}
                        st.session_state.unified_collection = add_to_vector_store(st.session_state.unified_collection, all_docs, "unified", metadata, chunk_size, overlap_percent)
                        st.session_state.indexed_files_count = len(all_docs)
                        # Track indexed files with details
                        st.session_state.indexed_files = []
                        for file_path, content in all_docs.items():
                            source_type = "Repository" if not file_path.startswith("uploaded:") else "Uploaded"
                            clean_path = file_path.replace("uploaded:", "") if file_path.startswith("uploaded:") else file_path
                            st.session_state.indexed_files.append({
                                'file_path': clean_path,
                                'source_type': source_type,
                                'content_length': len(content),
                                'chunks_estimated': (len(content) // chunk_size) + 1
                            })
                        track_index_built(file_count=len(all_docs), source_type="unified")
                        st.success(f"✅ Indexing complete! {st.session_state.indexed_files_count} total documents indexed.")
                    except Exception as e:
                        st.error(f"Indexing Error: {e}")
                else:
                    st.warning("No documents found to index.")

    with col2:
        if st.button("🗑️ Clear Index"):
            st.session_state.unified_collection = None
            st.session_state.messages = []
            st.session_state.sources = []
            st.session_state.indexed_files_count = 0
            st.session_state.excluded_files = []
            st.session_state.indexed_files = []
            st.session_state.repo_url = ""
            try:
                from simple_rag import get_chroma_client
                client = get_chroma_client()
                client.delete_collection("unified_sagevault")
            except Exception as e:
                print(f"Could not delete collection: {e}")
            st.success("Index cleared.")
            st.rerun()

    st.markdown("---")
    st.subheader("Indexing Status")
    if st.session_state.indexed_files_count > 0:
        st.info(f"**{st.session_state.indexed_files_count}** files are currently indexed.")
        if st.session_state.indexed_files:
            with st.expander(f"**{len(st.session_state.indexed_files)}** files were indexed"):
                df = pd.DataFrame(st.session_state.indexed_files)
                st.dataframe(df, width='stretch', hide_index=True)
    if st.session_state.excluded_files:
        with st.expander(f"**{len(st.session_state.excluded_files)}** files were excluded"):
            df = pd.DataFrame(st.session_state.excluded_files).head(20)
            st.dataframe(df, width='stretch', hide_index=True)

# --- Right Column: Chat Interface ---
with right_column:
    st.subheader("Conversational Chat")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask a question about the indexed content..."):
        if st.session_state.unified_collection is None:
            st.warning("Please index some documents before asking questions.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # 1. Search for relevant sources (with automatic security protection)
                    search_result = secure_rag_search(
                        lambda q, collection, k: search_vector_store(collection, q, k=k),
                        prompt, st.session_state.unified_collection, k=5
                    )
                    
                    # Handle security automatically
                    if "error" in search_result:
                        st.error(f"🔒 Security: {search_result['error']}")
                        st.session_state.messages.append({"role": "assistant", "content": "Query blocked for security reasons."})
                    else:
                        search_results = search_result["results"]
                        # Show security warnings if any (automatic)
                        for warning in search_result.get("warnings", []):
                            st.warning(f"🔒 Security Notice: {warning}")
                        
                        st.session_state.sources = search_results # Update sources for display
                        
                        # 2. Construct secure prompt for LLM (automatic security)
                        # Handle different possible key formats from search results
                        context_parts = []
                        for r in search_results:
                            # Check which key exists for the file path
                            file_path = r.get('file_path') or r.get('path') or r.get('source') or 'Unknown'
                            text = r.get('text', '')
                            context_parts.append(f"Source: {file_path}\n\n{text}")
                        context = "\n\n".join(context_parts)
                        llm_prompt = f"""{SECURE_SYSTEM_PROMPT}
                        
                        Context:
                        {context}
                        
                        Question: {prompt}
                        
                        Answer:"""

                        # 3. Call LLM and automatically secure response
                        response = call_llm(provider, api_key, llm_prompt)
                        
                        # Automatic security processing (transparent to user)
                        secure_resp = SecurityMiddleware.secure_response(response, search_results)
                        st.markdown(secure_resp["content"])
                        
                        # Show security info if needed (automatic)
                        display_security_info(secure_resp)
                        
                        st.session_state.messages.append({"role": "assistant", "content": secure_resp["content"]})
                    track_question_asked(provider_type=provider)
                    st.rerun() # Rerun to update the source display below


# --- Full-Width Sections Below ---
st.markdown("---")
st.subheader("📚 Sources")
st.markdown("""
> **About Similarity Scores & Provenance:**
> - *Similarity Score* measures how closely each source matches your question (range: 0.00–1.00; higher is more relevant).
> - *Provenance* indicates where the information came from (e.g., Repo, Download) for full transparency.
> - Downloaded documents are always shown as 📄 Download: [filename]. Repository files are shown as 🔍 Repo: [repo]/[filename].
> - For best results, refer to uploaded files as 'Download' in your questions.
""")
if st.session_state.sources:
    # Group sources: downloads first, then repo
    download_sources = [s for s in st.session_state.sources if (s.get('file_path') or s.get('path') or '').startswith('uploaded:')]
    repo_sources = [s for s in st.session_state.sources if not (s.get('file_path') or s.get('path') or '').startswith('uploaded:')]
    all_sources = download_sources + repo_sources
    for i, source in enumerate(all_sources):
        file_path = source.get('file_path') or source.get('path') or source.get('source') or 'Unknown'
        similarity = source.get('similarity', 0.0)
        source_type = source.get('source_type', 'unknown')
        provenance_chip = f"Provenance: Download" if file_path.startswith('uploaded:') else f"Provenance: Repo"
        # Display name and icon
        if file_path.startswith('uploaded:'):
            clean_filename = file_path.replace('uploaded:', '')
            display_name = f"📄 Download: {clean_filename}"
        else:
            repo_name = "Repository"
            if st.session_state.repo_url:
                try:
                    owner, repo = parse_github_url(st.session_state.repo_url)
                    repo_name = repo
                except:
                    repo_name = "Repository"
            display_name = f"🔍 Repo: {repo_name}/{file_path}"
        url = source.get('github_url')
        if not url and st.session_state.repo_url and not file_path.startswith('uploaded:'):
            url = f"https://github.com/{'/'.join(parse_github_url(st.session_state.repo_url))}/blob/main/{file_path}"
        with st.expander(f"**{i+1}. {display_name}** (Similarity: {similarity:.2f})"):
            st.markdown(f"`{provenance_chip}`")
            if url:
                st.markdown(f"[View on GitHub]({url})")
            elif file_path.startswith('uploaded:'):
                st.markdown(f"📎 **Source Type:** Uploaded Document")
            st.code(source['text'], language='text')
else:
    st.info("Source details will appear here after you ask a question.")

st.markdown("---")
with st.expander("📊 Session Analytics"):
    stats = get_session_summary()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Questions Asked", stats.get('questions_asked', 0))
    with col2:
        st.metric("Indexes Built", stats.get('indexes_built', 0))
    with col3:
        st.metric("Session Duration", f"{stats.get('session_duration_minutes', 0)} min")
    if st.button("Clear Analytics"):
        clear_analytics()
        st.rerun()