"""GitHub GuideBot - Clean RAG MVP with Document Upload"""
import streamlit as st
import requests
from urllib.parse import urlparse
from typing import Dict, List, Tuple
import os
import sys
import io

# Import our clean RAG utilities
from simple_rag import create_vector_store, search_vector_store

# Document processing imports
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document
except ImportError:
    Document = None

# Configure Streamlit
st.set_page_config(
    page_title="GitHub GuideBot - RAG MVP",
    page_icon="🤖",
    layout="wide"
)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF file"""
    if not PyPDF2:
        return "PyPDF2 not installed - cannot process PDF files"
    
    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX file"""
    if not Document:
        return "python-docx not installed - cannot process DOCX files"
    
    try:
        doc_file = io.BytesIO(file_bytes)
        doc = Document(doc_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        return f"Error processing DOCX: {str(e)}"

def extract_text_from_file(uploaded_file) -> Tuple[str, str]:
    """Extract text from uploaded file based on file type"""
    file_extension = uploaded_file.name.lower().split('.')[-1]
    file_bytes = uploaded_file.read()
    
    if file_extension == 'pdf':
        text = extract_text_from_pdf(file_bytes)
    elif file_extension == 'docx':
        text = extract_text_from_docx(file_bytes)
    elif file_extension in ['txt', 'md', 'py', 'js', 'html', 'css', 'json', 'yml', 'yaml']:
        try:
            text = file_bytes.decode('utf-8', errors='ignore')
        except:
            text = "Error: Could not decode text file"
    else:
        text = f"Unsupported file type: {file_extension}"
    
    return uploaded_file.name, text

def parse_github_url(url: str) -> Tuple[str, str]:
    """Extract owner and repo from GitHub URL"""
    parsed = urlparse(url)
    if not parsed.path:
        raise ValueError("Invalid GitHub URL")
    
    parts = [p for p in parsed.path.split('/') if p]
    if len(parts) < 2:
        raise ValueError("URL must be in format: https://github.com/owner/repo")
    
    return parts[0], parts[1]

def fetch_github_files(owner: str, repo: str, max_files: int = 100, github_token: str = None) -> Dict[str, str]:
    """Fetch text files from GitHub repository"""
    files = {}
    
    # Set up headers with authentication if token provided
    headers = {}
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    # Get repository tree
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
    response = requests.get(tree_url, headers=headers, timeout=30)
    
    if response.status_code != 200:
        # Try master branch
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/master?recursive=1"
        response = requests.get(tree_url, headers=headers, timeout=30)
    
    if response.status_code != 200:
        raise Exception(f"Could not access repository: {response.status_code}")
    
    tree_data = response.json()
    
    # Filter for text files - expanded list
    text_extensions = {
        # Documentation
        '.md', '.txt', '.rst', '.adoc', '.wiki',
        # Programming languages
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp', '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
        # Web technologies  
        '.css', '.html', '.htm', '.scss', '.sass', '.less',
        # Configuration
        '.json', '.yml', '.yaml', '.xml', '.toml', '.cfg', '.ini', '.conf', '.config',
        # Shell scripts
        '.sh', '.bash', '.zsh', '.ps1', '.bat', '.cmd',
        # Other common text files
        '.sql', '.r', '.m', '.pl', '.lua', '.vim', '.dockerfile'
    }
    
    # Also include files without extensions that are likely text (like README, LICENSE, etc.)
    common_text_files = {'readme', 'license', 'changelog', 'contributing', 'authors', 'credits', 'makefile', 'dockerfile', 'requirements'}
    
    count = 0
    
    for item in tree_data.get('tree', []):
        if item['type'] != 'blob' or count >= max_files:
            continue
            
        path = item['path']
        filename = path.lower()
        # Check if it's a text file by extension or by common filename
        is_text_file = (
            any(filename.endswith(ext) for ext in text_extensions) or
            any(common_name in filename for common_name in common_text_files)
        )
        
        if not is_text_file:
            continue
            
        # Fetch file content
        try:
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{path}"
            file_response = requests.get(raw_url, headers=headers if github_token else {}, timeout=15)
            
            if file_response.status_code != 200:
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{path}"
                file_response = requests.get(raw_url, headers=headers if github_token else {}, timeout=15)
            
            if file_response.status_code == 200 and len(file_response.content) < 100000:  # Max 100KB
                try:
                    content = file_response.content.decode('utf-8', errors='ignore')
                    if content.strip():
                        files[path] = content
                        count += 1
                except:
                    continue
        except:
            continue
    
    return files

def call_llm(provider: str, api_key: str, prompt: str) -> str:
    """Call LLM with the given prompt"""
    if not api_key:
        return "Please provide an API key to get AI-generated answers."
    
    if provider == "Groq":
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Groq API error: {str(e)}"
    
    elif provider == "OpenAI":
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenAI API error: {str(e)}"
    
    return "Unknown provider selected."

# Main UI
st.title("🤖 GitHub GuideBot - RAG MVP")
st.markdown("Ask questions about any public GitHub repository!")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    provider = st.selectbox("LLM Provider", ["None", "Groq", "OpenAI"])
    api_key = st.text_input("API Key", type="password", 
                           help="Your API key (stored only for this session)")
    
    st.markdown("---")
    st.subheader("🔑 GitHub Token (Optional)")
    github_token = st.text_input(
        "GitHub Personal Access Token", 
        type="password",
        help="Optional: Increases API rate limits and access to private repos"
    )
    
    st.markdown("---")
    
    # Document Upload Section
    st.subheader("📄 Upload Documents")
    uploaded_files = st.file_uploader(
        "Choose files", 
        type=['pdf', 'docx', 'txt', 'md', 'py', 'js', 'html', 'css', 'json', 'yml', 'yaml'],
        accept_multiple_files=True,
        help="Upload documents to include in your knowledge base"
    )
    
    if uploaded_files:
        st.success(f"📁 {len(uploaded_files)} file(s) ready")
        if st.button("🔍 Index Documents", type="secondary", use_container_width=True):
            with st.spinner("Processing uploaded documents..."):
                # Process uploaded files
                documents = []
                for uploaded_file in uploaded_files:
                    filename, text = extract_text_from_file(uploaded_file)
                    if text and not text.startswith("Error"):
                        documents.append({
                            'content': text,
                            'source': f"uploaded:{filename}",
                            'url': f"file://{filename}"
                        })
                        st.info(f"✅ {filename}")
                    else:
                        st.warning(f"❌ {filename}: {text}")
                
                if documents:
                    # Convert to format expected by create_vector_store (Dict[str, str])
                    doc_dict = {}
                    for doc in documents:
                        doc_dict[doc['source']] = doc['content']
                    
                    # Create vector store for uploaded docs
                    vector_store = create_vector_store(doc_dict, "uploaded_docs")
                    st.session_state.vector_store = vector_store
                    st.session_state.documents = documents
                    st.success(f"🎉 Indexed {len(documents)} documents!")
    
    st.markdown("---")
    st.markdown("**How to use:**")
    st.markdown("1. Paste a GitHub repo URL OR upload documents")
    st.markdown("2. Click the respective Index button")
    st.markdown("3. Ask questions about the content")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    repo_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/owner/repository",
        help="Enter a public GitHub repository URL"
    )

with col2:
    st.write("")  # Spacing
    index_button = st.button("🔍 Index Repository", type="primary", use_container_width=True)

# Initialize session state
if "collection" not in st.session_state:
    st.session_state.collection = None
if "repo_info" not in st.session_state:
    st.session_state.repo_info = None
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "documents" not in st.session_state:
    st.session_state.documents = []

# Index repository
if index_button and repo_url:
    try:
        with st.spinner("Indexing repository..."):
            # Parse URL
            owner, repo = parse_github_url(repo_url)
            
            # Fetch files
            files = fetch_github_files(owner, repo, github_token=github_token)
            
            if not files:
                st.error("No suitable text files found in repository")
            else:
                # Create vector store
                collection = create_vector_store(files, f"{owner}_{repo}")
                
                # Store in session
                st.session_state.collection = collection
                st.session_state.repo_info = {"owner": owner, "repo": repo, "files": len(files)}
                
                # Show what files were indexed
                with st.expander("📁 Files Indexed", expanded=False):
                    st.write(f"**Total files indexed: {len(files)}**")
                    for i, (file_path, content) in enumerate(files.items()):
                        char_count = len(content)
                        st.write(f"{i+1}. `{file_path}` ({char_count:,} characters)")
                        if i >= 9:  # Show first 10 files
                            remaining = len(files) - 10
                            if remaining > 0:
                                st.write(f"... and {remaining} more files")
                            break
                
                st.success(f"✅ Successfully indexed {len(files)} files from {owner}/{repo}")
                
    except Exception as e:
        st.error(f"Error indexing repository: {str(e)}")

# Q&A Section - works with both GitHub repos and uploaded documents
if st.session_state.collection is not None or st.session_state.vector_store is not None:
    st.markdown("---")
    st.subheader("❓ Ask Questions")
    
    question = st.text_area(
        "Your Question",
        placeholder="What does this repository/document contain? How do I use it? What are the main components?",
        height=100
    )
    
    if st.button("Get Answer", type="primary") and question:
        try:
            results = []
            
            # Search GitHub repository if indexed
            if st.session_state.collection is not None:
                repo_results = search_vector_store(st.session_state.collection, question, k=3)
                results.extend(repo_results)
            
            # Search uploaded documents if indexed  
            if st.session_state.vector_store is not None:
                doc_results = search_vector_store(st.session_state.vector_store, question, k=3)
                # Convert doc results to match repo results format
                for doc_result in doc_results:
                    results.append({
                        'file_path': doc_result.get('source', 'uploaded_document'),
                        'text': doc_result.get('text', ''),
                        'url': doc_result.get('url', ''),
                        'similarity': doc_result.get('similarity', 0.0)
                    })
            
            if not results:
                st.warning("No relevant information found.")
            else:
                # Generate AI answer first
                if provider != "None" and api_key:
                    # Use top 3 most relevant results for context
                    sorted_results = sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)[:3]
                    context = "\n\n".join([f"Source: {r['file_path']}\n{r['text']}" for r in sorted_results])
                    
                    prompt = f"""Based on the following context from documents and code repositories, answer this question: {question}

Context:
{context}

Please provide a clear, helpful answer based only on the provided context. If you can't answer based on the context, say so."""

                    with st.spinner("Generating answer..."):
                        answer = call_llm(provider, api_key, prompt)
                        st.markdown("### 🤖 AI Answer")
                        st.markdown(answer)
                        st.markdown("---")  # Separator between answer and sources
                else:
                    st.info("💡 Set up an LLM provider in the sidebar to get AI-generated answers!")
                    st.markdown("---")  # Separator
                
                # Show sources below the answer
                with st.expander("📚 Sources", expanded=True):  # Show expanded to see what files are being used
                    st.write(f"**Found {len(results)} relevant sources**")
                    for i, result in enumerate(results[:5]):  # Show top 5
                        file_path = result['file_path']
                        similarity = result.get('similarity', 0.0)
                        
                        # Handle different source types
                        if file_path.startswith("uploaded:"):
                            # Uploaded document
                            clean_name = file_path.replace("uploaded:", "")
                            st.markdown(f"📄 **{clean_name}** (uploaded document, similarity: {similarity:.3f})")
                        elif st.session_state.repo_info and not file_path.startswith("uploaded:"):
                            # GitHub repository file  
                            owner = st.session_state.repo_info['owner']
                            repo = st.session_state.repo_info['repo']
                            github_link = f"https://github.com/{owner}/{repo}/blob/main/{file_path}"
                            st.markdown(f"📁 **[{file_path}]({github_link})** (GitHub, similarity: {similarity:.3f})")
                        else:
                            # Other source
                            st.markdown(f"📋 **{file_path}** (similarity: {similarity:.3f})")
                        
                        # Show text preview with more context
                        text_preview = result['text'][:500] + "..." if len(result['text']) > 500 else result['text']
                        st.code(text_preview, language="text")
                    
        except Exception as e:
            st.error(f"Error processing question: {str(e)}")

else:
    st.info("👆 Index a GitHub repository or upload documents to get started!")
    st.markdown("**Getting Started:**")
    st.markdown("1. 📁 **For GitHub repos:** Enter a repository URL and click 'Index Repository'")
    st.markdown("2. 📄 **For documents:** Use the sidebar to upload PDF, Word, or text files")
    st.markdown("3. ❓ **Ask questions** once your content is indexed!")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit, ChromaDB, and Sentence Transformers")