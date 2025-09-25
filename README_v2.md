# GitHub GuideBot - RAG MVP

**Intelligent Document Analysis with Retrieval-Augmented Generation**

Transform how you explore GitHub repositories and analyze documents with AI-powered question answering, multi-source indexing, and comprehensive security controls.

---

## 🚀 What is GitHub GuideBot?

GitHub GuideBot is a powerful **Retrieval-Augmented Generation (RAG)** application that allows you to:

- **📂 Analyze GitHub Repositories**: Index and query any public GitHub repository
- **📄 Process Documents**: Upload and analyze PDF, DOCX, and text files  
- **🔍 Multi-Source Querying**: Ask questions across both repositories and uploaded documents simultaneously
- **🛡️ Security-First**: Advanced security controls with optional override for professionals
- **⚡ Configurable Processing**: Customizable text chunking and semantic search parameters

## ✨ Key Features

### 🎯 **Dual-Mode Analysis**
- **Repository Mode**: Fetch and index files from any public GitHub repository
- **Document Upload**: Process local files (PDF, DOCX, code files, configuration files)
- **Combined Analysis**: Query both sources in a single session for comprehensive insights

### 🧠 **Advanced RAG Engine** 
- **Semantic Search**: Uses SentenceTransformers with all-MiniLM-L6-v2 embeddings
- **Smart Chunking**: Configurable chunk sizes (200-1500 characters) with overlap control
- **README Prioritization**: Ensures documentation context is always included in results
- **Vector Storage**: ChromaDB-powered similarity search with cosine distance

### 🔒 **Enterprise-Grade Security**
- **File Type Filtering**: Comprehensive allowlist of safe text/code file types
- **Security Override**: Professional-grade risk assessment with informed consent
- **Content Sanitization**: Automatic redaction of sensitive information
- **Session Security**: API keys stored only in memory, never persisted

### 🤖 **Multi-LLM Support**
- **Groq**: Fast inference with Llama-3.1-8b-instant
- **OpenAI**: Premium responses with GPT-4o-mini
- **Flexible Configuration**: Easy provider switching in the UI

## 📁 Supported File Types

### **Code & Scripts**
`.py` `.js` `.ts` `.jsx` `.tsx` `.java` `.cpp` `.c` `.h` `.hpp` `.cs` `.php` `.rb` `.go` `.rs` `.swift` `.kt` `.scala` `.ipynb` `.sh` `.bash` `.zsh` `.sql`

### **Web Technologies**  
`.html` `.htm` `.css` `.scss` `.sass` `.less`

### **Configuration & Data**
`.json` `.yml` `.yaml` `.xml` `.toml` `.cfg` `.ini` `.conf` `.config` `.env`

### **Documentation**
`.md` `.txt` `.rst` `.adoc` `.wiki` + special files (README, LICENSE, CHANGELOG, etc.)

### **Documents** (Upload Only)
`PDF` `DOCX` - Full text extraction with error handling

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ (tested up to 3.12)
- API key for Groq or OpenAI
- Optional: GitHub Personal Access Token for higher rate limits

### Installation

```bash
# Clone the repository
git clone https://github.com/mwill20/github-guidebot.git
cd github-guidebot

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux  
source .venv/bin/activate

# Install dependencies
pip install -r requirements_clean.txt

# Launch the application
streamlit run streamlit_app_clean.py
```

The app will open in your browser at `http://localhost:8501`

## 📖 Usage Guide

### **🔍 Analyzing GitHub Repositories**

1. **Enter Repository URL**: Paste any public GitHub repository URL
2. **Configure Settings** (Optional):
   - Add GitHub Personal Access Token for higher API limits
   - Adjust chunk size (200-1500 chars, default: 500)
   - Set chunk overlap (0-50%, default: 10%)
3. **Click "🔍 Analyze Repository"**
4. **Review Indexed Files**: Expand the file list to see what was processed
5. **Ask Questions**: Query the repository content using natural language

### **📄 Uploading Documents**

1. **Select Files**: Use the sidebar file uploader
2. **Supported Formats**: PDF, DOCX, TXT, MD, code files, config files
3. **Click "🔍 Index Documents"**
4. **Multi-File Analysis**: Upload multiple documents for comprehensive analysis

### **🔗 Multi-Source Queries**

- Index both a repository AND upload documents in the same session
- Ask questions that span both sources
- Get unified results with clear source attribution

### **⚙️ Configuration Options**

#### **RAG Settings**
- **Chunk Size**: Control text segment size for processing (200-1500 characters)
- **Overlap**: Set overlap between chunks for better continuity (0-50%)

#### **LLM Configuration**  
- **Provider**: Choose between Groq (fast) or OpenAI (premium)
- **API Key**: Secure session-only storage

#### **GitHub Integration**
- **Personal Access Token**: Optional for 5000 requests/hour vs 60 requests/hour

## 🛡️ Security Features

### **🔒 File Security**
- **Safe Type Filtering**: Only processes known safe file types
- **Size Limits**: Files over 100KB are truncated
- **Binary Blocking**: Automatically rejects executables, archives, media files

### **⚠️ Security Override System**
For security professionals and advanced users:

- **Risk Assessment**: Identifies potentially dangerous files
- **Risk Categories**: HIGH (executables), MEDIUM (binaries/suspicious scripts), LOW (unknown types)
- **Informed Consent**: Clear warnings with explicit user confirmation required
- **Professional Use**: Enables controlled analysis of suspicious content

### **🔐 Content Protection**  
- **Input Sanitization**: Multi-layer filtering before processing
- **Secret Redaction**: Automatic removal of API keys, tokens, credentials
- **LLM Safety**: System instructions prevent code execution
- **Session Isolation**: No persistent storage of sensitive data

## 🏗️ Architecture

### **Core Components**

- **`streamlit_app_clean.py`**: Main application interface and orchestration
- **`simple_rag.py`**: Clean RAG utilities with ChromaDB and embeddings
- **`requirements_clean.txt`**: Minimal production dependencies

### **Legacy Components (app/ directory)**
- **`streamlit_app.py`**: Original full-featured app with coaching mode
- **`security_utils.py`**: Advanced security controls and content filtering  
- **`memory_orchestrator.py`**: Persistent memory and context management
- **`planner.py`**: Repository walkthrough and setup guidance

### **Technology Stack**

- **Frontend**: Streamlit for interactive web interface
- **Vector Database**: ChromaDB 0.4.15 for similarity search
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- **LLM Providers**: Groq (Llama-3.1-8b-instant), OpenAI (GPT-4o-mini)
- **Document Processing**: PyPDF2, python-docx for file extraction

## 🧪 Testing

### **Run Enhancement Tests**
```bash
python test_enhancements.py
```
Tests configurable chunking, README prioritization, file security, and multi-source indexing.

### **Run Security Override Tests**  
```bash
python test_security_override.py
```
Validates risk assessment and security warning system.

### **Run Full Test Suite**
```bash
pytest -v
```

## 🔧 Development

### **Project Structure**
```
github-guidebot/
├── streamlit_app_clean.py     # Main RAG application  
├── simple_rag.py             # Core RAG utilities
├── requirements_clean.txt    # Production dependencies
├── app/                      # Legacy full-featured version
├── tests/                    # Test suite
├── security.md              # Security documentation
└── README.md                # This file
```

### **Key Features for Developers**
- **Modular Design**: Clean separation between RAG engine and UI
- **Singleton Patterns**: Efficient resource management for ChromaDB and embeddings
- **Error Handling**: Comprehensive exception handling and user feedback
- **Security First**: Multiple layers of input validation and content filtering

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**: Follow the existing code style and patterns  
4. **Add tests**: Ensure new features have appropriate test coverage
5. **Run tests**: `python test_enhancements.py && pytest`
6. **Commit changes**: `git commit -m 'Add amazing feature'`
7. **Push to branch**: `git push origin feature/amazing-feature`
8. **Open Pull Request**: Describe your changes and include test results

## 📋 Requirements

### **Production Dependencies**
```
streamlit>=1.28.0          # Web interface
requests>=2.28.0           # HTTP client for GitHub API  
sentence-transformers>=2.2.0  # Embeddings model
chromadb==0.4.15          # Vector database
groq>=0.9.0               # Groq LLM API
openai>=1.40.0            # OpenAI API
numpy>=1.24.0             # Numerical computing
```

### **Optional Dependencies**
```
PyPDF2>=3.0.1             # PDF text extraction
python-docx>=1.2.0        # DOCX text extraction  
lxml>=6.0.2               # XML processing for documents
```

## 🔍 FAQ

**Q: Can I analyze private repositories?**  
A: Currently only public repositories are supported. Private repo support may be added in future versions.

**Q: What's the difference between the clean app and the full app?**  
A: `streamlit_app_clean.py` focuses on core RAG functionality. The full app (`app/streamlit_app.py`) includes additional features like coaching mode and advanced memory management.

**Q: How secure is the security override feature?**  
A: The override system is designed for security professionals. It provides clear risk assessment and requires explicit user consent. All decisions are logged and risky files are clearly flagged.

**Q: Can I customize the embedding model?**  
A: Currently uses all-MiniLM-L6-v2. Model customization can be added by modifying the `get_embeddings_model()` function in `simple_rag.py`.

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **Streamlit** for the excellent web framework
- **ChromaDB** for vector storage and similarity search  
- **Sentence Transformers** for semantic embeddings
- **Groq** and **OpenAI** for LLM inference
- **GitHub** for repository access via their API

---

**Built with ❤️ for developers, researchers, and security professionals who need intelligent document analysis.**