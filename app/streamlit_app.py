import re, requests, textwrap
import streamlit as st

st.set_page_config(page_title="GitHub GuideBot", layout="wide")
st.title("GitHub GuideBot — learn GitHub by doing")

url = st.text_input("Public GitHub repo URL", placeholder="https://github.com/owner/repo")
aud = st.selectbox("Audience", ["Beginner","Technical","Mixed"])
st.caption("Keys are not logged or stored. Public repos only.")

def parse_repo(u):
    m = re.match(r"https?://github\.com/([^/\s]+)/([^/\s#]+)", u or "")
    return (m.group(1), m.group(2)) if m else (None, None)

def gh_tree(owner, repo):
    head = requests.get(f"https://api.github.com/repos/{owner}/{repo}", timeout=10).json()
    ref = head.get("default_branch", "main")
    tree = requests.get(f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1", timeout=10).json()
    return ref, tree.get("tree", [])

def summarize_tree(items, audience="Beginner"):
    files = [i["path"] for i in items if i.get("type")=="blob"]
    dirs = sorted({p.split("/")[0] for p in files if "/" in p})
    txt = []
    if audience=="Beginner":
        txt.append("A repository is a project folder tracked by Git on GitHub.")
        txt.append(f"It has {len(files)} files across {len(dirs)} top-level folders.")
        if "README.md" in files: txt.append("README.md explains the project and usage.")
    else:
        txt.append(f"{len(files)} files, {len(dirs)} top directories.")
    return "\n".join(txt), files, dirs

def safe_allowlisted(path):
    allow = (".md",".txt",".py",".ipynb",".toml",".cfg",".json",".yml",".yaml",".ini",".rst",".csv",".tsv",".env.example")
    deny  = (".env",".pem",".key",".pfx",".keystore")
    return path.endswith(allow) and not path.endswith(deny)

def fetch_small_text(owner, repo, path, ref):
    raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"
    r = requests.get(raw, timeout=10)
    if r.status_code==200 and len(r.text) < 80000:
        return r.text
    return ""

with st.expander("What is a GitHub repository?", expanded=True if not url else False):
    st.write("We’ll fetch a public repo, map its structure, and explain how to run it.")

if st.button("Analyze") and url:
    owner, repo = parse_repo(url)
    if not owner:
        st.error("Enter a valid URL like https://github.com/owner/repo")
    else:
        ref, items = gh_tree(owner, repo)
        summary, files, dirs = summarize_tree(items, aud)
        st.subheader("Repo Overview"); st.write(summary)
        st.write({"default_branch": ref, "top_dirs": dirs[:10]})
        sample = [p for p in files if safe_allowlisted(p)][:30]
        corpus = {p: fetch_small_text(owner, repo, p, ref)[:5000] for p in sample}
        corpus = {k:v for k,v in corpus.items() if v}
        st.session_state["corpus"] = corpus
        st.success(f"Loaded {len(corpus)} text files for basic Q&A (demo).")

if "corpus" in st.session_state:
    q = st.text_input("Ask a question about this repo")
    if st.button("Answer") and q:
        hits = []
        for path, txt in st.session_state["corpus"].items():
            score = sum(txt.lower().count(w) for w in set(re.findall(r"\w+", q.lower())))
            if score: hits.append((score, path, txt[:800]))
        hits.sort(reverse=True)
        if hits:
            score, path, snippet = hits[0]
            st.markdown("**Answer (demo):**")
            st.write(textwrap.shorten(snippet, width=600, placeholder=" ..."))
            st.caption(f"Source: {path}")
        else:
            st.info("No matches. Try simpler terms or open README.md.")
st.divider(); st.caption("Security: session-only keys, public repos, allowlisted files, size caps, no code execution.")
