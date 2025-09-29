import os, re, requests, sys
import streamlit as st
from urllib.parse import urlparse
from typing import List, Dict, Tuple

# --- Security & Memory (reuse existing modules) ---
try:
    from .security.security_utils import penalize_suspicious, redact_secrets
except ImportError:
    from app.security.security_utils import penalize_suspicious, redact_secrets
try:
    from .memory_orchestrator import update_ledger
except ImportError:
    try:
        from memory_orchestrator import update_ledger
    except Exception:  # noqa: F401
        def update_ledger(*args, **kwargs):
            return {}

# --- Pre-config: silence Chroma telemetry BEFORE any chromadb import via rag_utils ---
os.environ.setdefault("ANONYMIZED_TELEMETRY", "false")
os.environ.setdefault("CHROMADB_DISABLE_TELEMETRY", "true")

# Early telemetry suppression - monkey patch before any import can trigger capture
def _noop_capture(*args, **kwargs):
    pass

# Pre-emptively patch common telemetry entry points with dynamic import hook
import sys
from importlib.abc import MetaPathFinder, Loader
from importlib.machinery import ModuleSpec

class TelemetryInterceptor:
    def __getattr__(self, name):
        # Return another interceptor for nested attribute access
        return TelemetryInterceptor()
    
    def __call__(self, *args, **kwargs):
        # Handle cases where the interceptor itself is called
        return TelemetryInterceptor()
    
    def __iter__(self):
        # Handle iteration attempts
        return iter([])
    
    def __bool__(self):
        return False
    
    def capture(self, *args, **kwargs):
        pass

class TelemetryImportHook(MetaPathFinder, Loader):
    """Intercepts ANY chromadb.telemetry.* import and returns our interceptor"""
    
    def find_spec(self, fullname, path, target=None):
        if fullname.startswith('chromadb.telemetry'):
            # Return a spec that will use our loader
            return ModuleSpec(fullname, self)
        return None
    
    def create_module(self, spec):
        # Return our interceptor as the module
        return TelemetryInterceptor()
    
    def exec_module(self, module):
        # Nothing to execute, our interceptor is ready to use
        pass

# Install the import hook BEFORE any chromadb import
if 'chromadb' not in sys.modules:
    # Install our custom import hook at the beginning of sys.meta_path
    sys.meta_path.insert(0, TelemetryImportHook())

# --- Quick module availability probes (avoid expensive imports) ---
def _probe_module(mod: str) -> bool:
    try:
        __import__(mod)
        return True
    except Exception:
        return False

_HAS_GROQ = _probe_module("groq")
_HAS_OPENAI = _probe_module("openai")

# --- Vector store (Chroma) helpers ---
try:
    from .rag_utils import build_store, retrieve
except ImportError:
    from rag_utils import build_store, retrieve

# --- Safety-oriented file policy ---
ALLOW = {".md", ".py", ".txt", ".rst", ".cfg", ".ini", ".toml", ".yaml", ".yml", ".js", ".ts"}
MAX_FILE_BYTES = 80_000
BRANCH_GUESS = ("main", "master")

def parse_repo(url: str) -> Tuple[str, str]:
    p = urlparse(url)
    parts = [x for x in (p.path or "").split("/") if x]
    if len(parts) < 2:
        raise ValueError("Use https://github.com/<owner>/<repo>")
    return parts[0], parts[1]

def gh_tree(owner: str, repo: str) -> Tuple[str, List[Dict]]:
    s = requests.Session(); s.headers["Accept"] = "application/vnd.github+json"
    for ref in BRANCH_GUESS:
        r = s.get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1", timeout=20)
        if r.status_code == 200:
            tree = [e for e in r.json().get("tree", []) if e.get("type") == "blob"]
            return ref, tree
    raise RuntimeError("Could not list repo tree (no main/master?)")

def is_text_path(path: str) -> bool:
    p = (path or "").lower()
    return any(p.endswith(ext) for ext in ALLOW)

def fetch_text_files(owner: str, repo: str, ref: str, tree: List[Dict]) -> List[Tuple[str, str, str]]:
    out: List[Tuple[str, str, str]] = []
    for e in tree:
        path = e.get("path", "")
        if not is_text_path(path):
            continue
        raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"
        r = requests.get(raw, timeout=20)
        if r.ok and len(r.content) <= MAX_FILE_BYTES:
            try:
                text = r.content.decode("utf-8", errors="ignore")
            except Exception:
                continue
            out.append((path, raw, text))
        if len(out) >= 200:
            break
    return out

# Chroma handles chunking/embeddings internally via rag_utils

# --- LLM connector (optional) ---
def answer_with_llm(provider: str, api_key: str, question: str, context: str) -> str:
    # Extractive fallback when no provider or missing key
    if (provider or "").lower() in ("none", "") or not api_key:
        return context[:1200] + "\n\n(Extractive fallback — select a provider and add an API key for a better answer.)"
    if provider == "Groq":
        has_groq = _probe_module("groq")  # re-check in case installed after first load
        if not has_groq:
            return (
                "(Groq SDK not importable at runtime. Python=" + sys.executable +
                "; ensure you installed inside this venv and restarted app. "
                "If you just pip installed, stop Streamlit and relaunch using: .venv\\Scripts\\python.exe -m streamlit run app/streamlit_app.py)"
            )
        try:
            from groq import Groq  # noqa: F401
        except Exception as e:
            return f"(Groq import failed unexpectedly: {e} | Python={sys.executable})"
        try:
            cli = Groq(api_key=api_key)
            r = cli.chat.completions.create(
                model="llama-3.1-70b-versatile",  # Updated to current supported model
                messages=[
                    {"role": "system", "content": "Answer ONLY from context. Cite filenames inline."},
                    {"role": "user", "content": f"Q: {question}\n\nContext:\n{context}"},
                ],
                temperature=0.2,
                max_tokens=500,
            )
            return r.choices[0].message.content
        except Exception as e:
            if "invalid_api_key" in str(e).lower() or "401" in str(e):
                return f"(Invalid Groq API key. Please check your API key and try again. Get a valid key from: https://console.groq.com/keys)"
            elif "rate_limit" in str(e).lower() or "429" in str(e):
                return f"(Groq rate limit exceeded. Please wait a moment and try again.)"
            else:
                return f"(Groq API error: {e})"
    if provider == "OpenAI":
        has_openai = _probe_module("openai")
        if not has_openai:
            return "(OpenAI SDK not importable in this interpreter. Install 'openai' in the active venv and restart.)"
        try:
            from openai import OpenAI  # noqa: F401
        except Exception as e:
            return f"(OpenAI import failed unexpectedly: {e} | Python={sys.executable})"
        try:
            cli = OpenAI(api_key=api_key)
            r = cli.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Answer ONLY from context. Cite filenames inline."},
                    {"role": "user", "content": f"Q: {question}\n\nContext:\n{context}"},
                ],
                temperature=0.2,
                max_tokens=500,
            )
            return r.choices[0].message.content
        except Exception as e:
            if "invalid_api_key" in str(e).lower() or "401" in str(e):
                return f"(Invalid OpenAI API key. Please check your API key and try again. Get a valid key from: https://platform.openai.com/api-keys)"
            elif "rate_limit" in str(e).lower() or "429" in str(e):
                return f"(OpenAI rate limit exceeded. Please wait a moment and try again.)"
            else:
                return f"(OpenAI API error: {e})"
    return "(Unknown provider; pick Groq, OpenAI, or None.)"

# --- UI ---
st.set_page_config(page_title="SageVault — RAG MVP", layout="wide")
st.title("SageVault — RAG MVP")

# Sidebar: provider, API key, chunking controls
with st.sidebar:
    st.header("LLM & Index Settings")
    provider = st.selectbox(
        "LLM Provider",
        ["Groq", "OpenAI", "None"],
        help="Choose a model for the final answer. None uses extractive fallback (no LLM).",
    )
    api_key = st.text_input(
        "API Key",
        type="password",
        help="Your key is used only in-session and never logged.",
    )
    if "chunk_size" not in st.session_state:
        st.session_state.chunk_size = 500
    if "overlap_pct" not in st.session_state:
        st.session_state.overlap_pct = 10
    chunk_size = st.slider(
        "Chunk size",
        min_value=300,
        max_value=1200,
        value=st.session_state.chunk_size,
        step=50,
        help="Characters per chunk (default 500).",
    )
    overlap_pct = st.slider(
        "Overlap %",
        min_value=0,
        max_value=30,
        value=st.session_state.overlap_pct,
        step=1,
        help="Percent overlap between chunks (default 10%).",
    )
    overlap_chars = int(round(chunk_size * overlap_pct / 100))
    st.caption(f"Effective overlap: {overlap_chars} chars")
    st.session_state.chunk_size = chunk_size
    st.session_state.overlap_pct = overlap_pct

    with st.expander("Runtime diagnostics", expanded=False):
        st.caption("Interpreter path:")
        st.code(sys.executable, language="text")
        st.caption("Installed modules detected at app start:")
        st.write({"groq": _HAS_GROQ, "openai": _HAS_OPENAI})
        st.caption("If a module shows False after installing, fully stop and restart Streamlit using the venv python executable.")

# Main area: URL input, Analyze button, and Q&A
repo_url = st.text_input(
    "Public GitHub repo URL",
    placeholder="https://github.com/owner/repo",
    help="Public repos only. We fetch safe, small text files (allowlist + 80KB cap) and embed locally.",
)
go = st.button("Analyze this repo")

question = st.text_area(
    "Ask about this repo",
    placeholder="What does this project do? How do I run it?",
)
ask = st.button("Ask")

ss = st.session_state
if go and repo_url:
    try:
        owner, repo = parse_repo(repo_url)
        ref, tree = gh_tree(owner, repo)
        files = fetch_text_files(owner, repo, ref, tree)
        corpus: Dict[str, str] = {path: txt for (path, _url, txt) in files}
        # Use sidebar chunking settings
        overlap_chars = int(round(st.session_state.chunk_size * st.session_state.overlap_pct / 100))
        collection = build_store(corpus, name="repo", chunk_size=st.session_state.chunk_size, overlap=overlap_chars)
        ss["collection"] = collection
        ss["repo_meta"] = {"owner": owner, "repo": repo, "ref": ref}
        st.success(f"Indexed {len(corpus)} files • chunk_size={st.session_state.chunk_size}, overlap={overlap_chars}")
        try:
            update_ledger("index_built", {"repo": f"{owner}/{repo}", "files": len(files)})
        except Exception:
            pass
    except Exception as e:
        st.warning(f"Indexing failed: {e}")

if ask:
    if "collection" not in ss:
        st.warning("No index yet. Paste a repo URL and click Analyze.")
    elif not (question or "").strip():
        st.warning("Ask a specific question.")
    else:
        # Security: check user prompt pattern
        try:
            qcheck = penalize_suspicious({"cmd": question})
            if isinstance(qcheck, dict) and qcheck.get("warning"):
                st.warning(qcheck["warning"])  # UI warn
        except Exception:
            pass

        hits = retrieve(ss["collection"], question, k=5)

        st.markdown("### Top sources")
        ctx: List[str] = []
        owner = ss.get("repo_meta", {}).get("owner")
        repo = ss.get("repo_meta", {}).get("repo")
        ref = ss.get("repo_meta", {}).get("ref", "main")
        for h in hits:
            path = h.get("path", "?")
            sim = h.get("similarity", 0.0)
            link = f"https://github.com/{owner}/{repo}/blob/{ref}/{path}" if owner and repo else path
            st.write(f"- **{path}** — similarity: `{sim:.3f}` • [view]({link})")
            ctx.append(f"[{path}] {h.get('text','')}")

        context = "\n\n".join(ctx[:4])
        context = redact_secrets(context)

        ans = answer_with_llm(provider, api_key, question, context)
        st.markdown("### Answer")
        st.write(ans)

        try:
            update_ledger("qa", {"q": question, "sources": [h.get("path") for h in hits]})
        except Exception:
            pass
