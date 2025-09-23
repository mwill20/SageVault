import re, requests, textwrap, hashlib, time
import streamlit as st

from rag_utils import build_store, retrieve
from llm_utils import call_llm
from prompts import SYSTEM_PROMPT
from security_utils import sanitize_text, redact_secrets, label_dangerous_commands, penalize_suspicious
from memory_orchestrator import assemble_context, update_ledger

GH_HEADERS = {"User-Agent": "github-guidebot"}


# --- constants / knobs ---
MAX_INDEX_FILES = 60           # cap number of files embedded
MAX_CHUNK_CONTEXT = 4800       # total context chars sent to LLM
CHUNK_PREVIEW = 1200           # per-chunk trim before concatenation
SYNTH_MAX_CHUNKS = 4           # number of top chunks to synthesize for fallback
README_PREVIEW_CHARS = 1800    # larger allowance for README overview grounding
SYNTH_JOINER = "\n---\n"      # separator between chunks in synthesized answer

# Housekeeping / rationale for recent additions:
# - README_PREVIEW_CHARS: README often carries project intent; giving it a larger
#   preview window improves high-level question accuracy ("what is this repo about?").
# - Session keys introduced:
#     readme_path : path of selected README (root README.* preferred)
#     readme_text : cached large slice (<=15k chars) used for:
#         * injecting a synthetic high-similarity README hit when semantic ranking misses it
#         * providing an extended single-chunk context for overview queries
#   Logic degrades gracefully if README not found (keys remain None).


# --- page config ---
st.set_page_config(page_title="GitHub GuideBot", layout="wide")


# --- UI helpers (Phase 3 polish) ---
def warn(msg: str):
    """Standardized warning with icon (replaces inline **WARN:** markers)."""
    st.warning(msg, icon="⚠️")


def show_provenance(pth: str, start: int | None = None, end: int | None = None, score: float | None = None):
    """Render a compact provenance badge for a cited chunk.

    Parameters
    ----------
    pth : str
        File path relative to repo root.
    start, end : int | None
        Optional (future) line range for the chunk.
    score : float | None
        Similarity score (0-1) from vector search after adjustments.
    """
    parts = [pth]
    if start is not None and end is not None:
        parts.append(f"lines {start}-{end}")
    if score is not None:
        parts.append(f"sim {score:.2f}")
    st.caption(" • ".join(parts))

# --- session state defaults for future LLM routing ---
if "llm_provider" not in st.session_state:
    st.session_state.llm_provider = "none"
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

st.title("GitHub GuideBot")
st.caption("Learn GitHub by doing — paste a public repo and explore.")

# Shorter inputs (layout no longer constrained by columns)
repo_url = st.text_input(
    "Public GitHub repo URL",
    placeholder="https://github.com/owner/repo",
    key="repo_url",
    help="Public repos only. Long URLs scroll inside this box."
)

audience = st.selectbox(
    "Audience",
    ["Beginner", "Technical", "Mixed"],
    index=0,
    key="audience",
)

analyze_clicked = st.button("Analyze", type="primary")

# --- Sidebar controls ---
with st.sidebar:
    st.header("LLM & Index Settings")
    # LLM Preferences
    llm_provider = st.selectbox(
        "Provider",
        ["Gemini", "Groq", "OpenAI", "Claude", "XAI", "OpenRouter", "none"],
        index=6,
        key="llm_select_sidebar",
    )
    api_key = st.text_input(
        f"{llm_provider} API Key" if llm_provider != "none" else "API Key",
        type="password",
        placeholder="sk-… / gsk_… / or_…",
        key="api_key_input_sidebar",
        help="Stored in session only; never logged."
    )
    st.session_state.llm_provider = llm_provider
    st.session_state.api_key = api_key

    st.divider()
    st.subheader("Advanced indexing")
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
        help="Characters per chunk; 500–800 recommended for balance."
    )
    overlap_pct = st.slider(
        "Overlap %",
        min_value=0,
        max_value=30,
        value=st.session_state.overlap_pct,
        step=1,
        help="Portion of characters repeated next chunk; ~10% keeps continuity."
    )
    overlap_chars = int(round(chunk_size * overlap_pct / 100))
    st.caption(f"Effective overlap: {overlap_chars} chars")
    st.session_state.chunk_size = chunk_size
    st.session_state.overlap_pct = overlap_pct
    st.session_state.overlap_chars = overlap_chars
    st.markdown(
        "**Guidance:** 500–800 chars + ~10% overlap = balanced.\n"
        "Smaller: ↑recall / ↑cost. Larger: ↓embeddings / risk of topic drift.\n"
        "Overlap >20% rarely helps; 0% can fragment sentences."
    )
    st.caption("Re-run Analyze after changes to rebuild index.")

# Preserve original variable names used later in the script
url = repo_url
aud = audience

# (LLM integration placeholder)  provider = st.session_state.llm_provider ; api_key = st.session_state.api_key
st.caption("Security: Keys are session-only and never logged. Public repos only.")

def parse_repo(u: str):
    u = (u or "").strip()
    m = re.match(r"https?://github\.com/([^/\s]+)/([^/\s#]+)", u)
    if not m: 
        return (None, None)
    owner, repo = m.group(1), m.group(2).removesuffix(".git")
    return owner, repo

def gh_tree(owner, repo):
    try:
        # HEAD/metadata request
        head = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers=GH_HEADERS,
            timeout=10,
        )
        if head.status_code != 200:
            st.error(f"GitHub error {head.status_code}: {head.json().get('message','')}")
            return "main", []

        ref = head.json().get("default_branch", "main")

        # Tree (recursive) request
        tree = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1",
            headers=GH_HEADERS,
            timeout=15,
        )
        if tree.status_code == 403:
            st.warning("GitHub rate limit hit. Try again in a minute or use a different repo.")
            return ref, []


        return ref, tree.json().get("tree", [])
    except requests.RequestException as e:
        st.error(f"Network error: {e}")
        return "main", []

def summarize_tree(items, audience="Beginner"):
    files = [i["path"] for i in items if i.get("type")=="blob"]
    dirs = sorted({p.split("/")[0] for p in files if "/" in p})
    txt = []
    if audience=="Beginner":
        txt.append("A repository is a project folder tracked by Git on GitHub.")
        txt.append(f"It has {len(files)} files across {len(dirs)} top-level folders.")
        if any(p.lower().startswith("readme") for p in files): txt.append("README.md explains the project and usage.")
    else:
        txt.append(f"{len(files)} files, {len(dirs)} top directories.")
    return "\n".join(txt), files, dirs

def safe_allowlisted(path):
    allow = (".md",".txt",".py",".ipynb",".toml",".cfg",".json",".yml",".yaml",".ini",".rst",".csv",".tsv",".env.example",".sh")
    deny  = (".env",".pem",".key",".pfx",".keystore")
    return path.endswith(allow) and not path.endswith(deny)

PRIORITY_PREFIXES = (
    "README", "readme", "LICENSE", "license",
    "requirements", "pyproject.toml", "environment.yml",
    "setup.", "Makefile"
)

def sort_priority(paths):
    # Priority: root README/important files, then other root .md, then the rest
    def rank(p):
        root = ("/" not in p)
        starts = any(p.startswith(pref) or p.lower().startswith(pref.lower()) for pref in PRIORITY_PREFIXES)
        is_root_md = root and p.lower().endswith(".md")
        return (
            0 if (root and starts) else
            1 if is_root_md else
            2
        )
    return sorted(paths, key=rank)

def fetch_small_text(owner, repo, path, ref):
    raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"
    r = requests.get(raw, headers=GH_HEADERS, timeout=10)
    if r.status_code == 200 and len(r.text) < 80_000:
        return r.text
    return ""

def synthesize_semantic_answer(hits, max_chunks=SYNTH_MAX_CHUNKS, joiner=SYNTH_JOINER, max_chars=1200):
    """Combine top-N semantic hits into a concise stitched answer.

    Truncates individual chunks (soft) and concatenates with a separator.
    This is a lightweight heuristic summarization before an LLM answer
    is available or as a fallback when no provider/key is configured.
    """
    if not hits:
        return ""
    parts = []
    for h in hits[:max_chunks]:
        txt = h["text"].strip()
        if len(txt) > max_chars:
            txt = txt[:max_chars].rsplit(" ", 1)[0] + " …"
        parts.append(txt)
    return joiner.join(parts)

with st.expander("What is a GitHub repository?", expanded=True if not url else False):
    st.write("We’ll fetch a public repo, map its structure, and explain how to run it.")

if analyze_clicked and url:
    owner, repo = parse_repo(url)
    if not owner:
        st.error("Enter a valid URL like https://github.com/owner/repo")
    else:
        ref, items = gh_tree(owner, repo)
        summary, files, dirs = summarize_tree(items, aud)
        st.subheader("Repo Overview"); st.write(summary)
        st.write({"default_branch": ref, "top_dirs": dirs[:10]})
        # Persist branch/ref & repo identity for later citation link building
        st.session_state["ref"] = ref
        st.session_state["repo_meta"] = {"owner": owner, "repo": repo}

        # --- Detect & cache README for strong grounding ---
        def _find_readme(paths):
            # prefer root README.* first, then any README.*
            root = [p for p in paths if "/" not in p]
            cand = [p for p in root if p.lower().startswith("readme")]
            if cand:
                return sorted(cand, key=len)[0]
            cand = [p for p in paths if p.lower().startswith("readme")]
            return sorted(cand, key=len)[0] if cand else None

        readme_path = _find_readme(files)
        st.session_state["readme_path"] = readme_path
        st.session_state["readme_text"] = None
        if readme_path:
            txt = fetch_small_text(owner, repo, readme_path, ref)
            # allow larger slice for README (it’s the overview)
            if txt:
                st.session_state["readme_text"] = txt[:15000]

        allow = [p for p in files if safe_allowlisted(p)]
        prioritized = sort_priority(allow)
        sample = prioritized[:MAX_INDEX_FILES]

        corpus = {}
        for p in sample:
            txt = fetch_small_text(owner, repo, p, ref)
            if txt:
                corpus[p] = txt[:5000]  # slice large files defensively
        st.session_state["corpus"] = corpus

        with st.expander(f"Indexed files ({len(corpus)})", expanded=False):
            st.write(list(corpus.keys()))

        if not corpus:
            st.warning("No indexable files found (allowlist/size limits). Try another repo or view README online.")
        else:
            st.success(f"Loaded {len(corpus)} text files.")
            # Compute hash of corpus (filenames + length) to reuse existing embedding index when unchanged
            corpus_hash = hashlib.sha256(
                str(
                    {
                        "files": sorted((k, len(v)) for k, v in corpus.items()),
                        "chunk_size": st.session_state.get("chunk_size"),
                        "overlap": st.session_state.get("overlap_chars"),
                    }
                ).encode()
            ).hexdigest()
            prev_hash = st.session_state.get("corpus_hash")
            if st.session_state.get("collection") and prev_hash == corpus_hash:
                st.info("Using cached semantic index (no content changes detected).")
            else:
                try:
                    with st.spinner("Embedding & indexing…"):
                        st.session_state["collection"] = build_store(
                            corpus,
                            chunk_size=st.session_state.get("chunk_size", 500),
                            overlap=st.session_state.get("overlap_chars", 50),
                        )
                    st.session_state["corpus_hash"] = corpus_hash
                    st.session_state["collection_built_at"] = time.time()
                    st.success("Semantic index ready.")
                except Exception as e:
                    st.error(f"Failed to build semantic index: {e}")
                    st.session_state.pop("collection", None)

# --- Semantic Q&A ---
hits = None  # ensure defined for later checks
if "collection" in st.session_state:
    q_raw = st.text_input("Ask a question about this repo")
    q = sanitize_text(q_raw, max_len=500)
    if st.button("Answer"):
        if not q.strip():
            st.info("Type a question first.")
        else:
            # fetch more candidates, then reorder to prioritize README/root files
            candidates = retrieve(st.session_state["collection"], q, k=16)
            # Apply injection + diversity filtering heuristics (mutates similarity)
            candidates = penalize_suspicious(candidates, text_key="text")

            def _path_priority(h):
                p = (h.get("path") or "").lower()
                if p.startswith("readme"): return 0
                if "/" not in p:          return 1   # root files
                return 2

            candidates_sorted = sorted(candidates, key=lambda h: (_path_priority(h), -h.get("similarity", 0.0)))
            hits = candidates_sorted[:SYNTH_MAX_CHUNKS]

            # Force README first when we have it
            rp = st.session_state.get("readme_path")
            rt = st.session_state.get("readme_text")
            if rp and rt:
                if not (hits and hits[0].get("path", "").lower().startswith("readme")):
                    readme_hit = {"path": rp, "chunk": 0, "text": rt[:CHUNK_PREVIEW], "similarity": 1.0}
                    seen = {rp}
                    rest = [h for h in hits if h.get("path") not in seen]
                    hits = [readme_hit] + rest[:SYNTH_MAX_CHUNKS - 1]

            # Heuristic: if user asks for high-level overview, bias to README only
            overview_terms = ("about", "overview", "summary", "describe", "purpose")
            if rp and rt and any(t in q.lower() for t in overview_terms):
                # Replace hits with a synthetic single README hit (extended preview)
                hits = [{
                    "path": rp,
                    "chunk": 0,
                    "text": rt[:README_PREVIEW_CHARS],
                    "similarity": 1.0,
                }]

            if not hits:
                st.info("No relevant chunks found. Try simpler terms like 'install', 'requirements', or 'usage'.")

    if hits:
        # Build context using memory hierarchy (episodic + window + ledger + optional summary)
        history = st.session_state.get("history", [])  # list of (q,a)
        summary_digest = st.session_state.get("summary_digest", "")
        ledger = st.session_state.get("ledger", [])
        cfg = {"policy": {"max_ctx_tokens": 3000}}
        context = assemble_context(q, hits, history, summary_digest, cfg, ledger=ledger)
        if len(context) > MAX_CHUNK_CONTEXT:
            # final char safeguard
            context = context[:MAX_CHUNK_CONTEXT].rsplit(" ", 1)[0] + " …"

        provider = st.session_state.llm_provider
        api_key = st.session_state.api_key

        llm_answer = None
        provider_used = False
        if provider and provider.lower() != "none" and api_key:
            with st.spinner(f"Querying {provider}…"):
                try:
                    llm_answer = call_llm(provider, api_key, q, context)
                    provider_used = True
                except Exception as e:
                    st.error(f"LLM call failed: {e}")

        if llm_answer:
            llm_answer = redact_secrets(llm_answer)
            llm_answer = label_dangerous_commands(llm_answer)
            st.markdown("**Answer (LLM):**")
            danger_present = any(seg.startswith("**WARN:**") for seg in llm_answer.split("\n"))
            if danger_present:
                warn("Potentially dangerous command or prompt injection pattern detected in generated answer. Review commands carefully before executing.")
            cleaned_lines = [ln for ln in llm_answer.splitlines() if not ln.startswith("**WARN:**")]  # drop inline markers
            st.write("\n".join(cleaned_lines))
            st.session_state.setdefault("history", []).append((q, llm_answer[:2000]))
            ledger_entry = {"q": q[:140], "a": llm_answer[:220]}
            updated = update_ledger(st.session_state, ledger_entry, cap=50)
            st.session_state["ledger"] = updated.get("ledger", [])
        else:
            fallback_reason = (
                "no provider selected" if provider.lower() == "none" else
                "missing API key" if provider and not api_key else
                "provider error; showing semantic fallback"
            )
            stitched = synthesize_semantic_answer(hits)
            st.markdown(f"**Answer (semantic synthesis – {fallback_reason})**")
            fallback_out = stitched or hits[0]["text"]
            fallback_out = redact_secrets(fallback_out)
            fallback_out = label_dangerous_commands(fallback_out)
            danger_present = any(seg.startswith("**WARN:**") for seg in fallback_out.split("\n"))
            if danger_present:
                warn("Potentially dangerous command or prompt injection pattern detected in synthesized answer.")
            cleaned_lines = [ln for ln in fallback_out.splitlines() if not ln.startswith("**WARN:**")]  # drop inline markers
            st.write("\n".join(cleaned_lines))
            st.session_state.setdefault("history", []).append((q, fallback_out[:2000]))
            ledger_entry = {"q": q[:140], "a": fallback_out[:220]}
            updated = update_ledger(st.session_state, ledger_entry, cap=50)
            st.session_state["ledger"] = updated.get("ledger", [])

        # Citations & provenance with inline snippet preview
        with st.expander("Context chunks & sources", expanded=False):
            meta = st.session_state.get("repo_meta", {})
            ref = st.session_state.get("ref", "main")
            owner = meta.get("owner")
            repo = meta.get("repo")
            for idx, h in enumerate(hits, start=1):
                file_path = h.get("path", "?")
                snippet = (h.get("text") or "").strip()
                if len(snippet) > 260:
                    snippet = snippet[:260].rsplit(" ", 1)[0] + " …"
                if owner and repo:
                    gh_url = f"https://github.com/{owner}/{repo}/blob/{ref}/{file_path}"
                    st.markdown(f"**{idx}. [{file_path}]({gh_url})**  (sim {h.get('similarity',0):.2f})")
                else:
                    st.markdown(f"**{idx}. {file_path}**  (sim {h.get('similarity',0):.2f})")
                st.code(snippet or "(empty)")
                show_provenance(file_path, score=h.get("similarity"))
else:
    st.info("Analyze a repo to build the index.")
