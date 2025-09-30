"""Quick smoke test for the sample data bundled with SageVault."""
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from simple_rag import create_vector_store, search_vector_store

REPO_DIR = BASE_DIR / "sample_repo"
DOCS_DIR = BASE_DIR / "docs"


def load_repository_documents() -> dict[str, str]:
    repo_docs: dict[str, str] = {}
    for path in REPO_DIR.rglob("*"):
        if path.is_file() and path.suffix in {".py", ".md", ".yml"}:
            repo_docs[str(path.relative_to(REPO_DIR))] = path.read_text(encoding="utf-8")
    return repo_docs


def load_uploaded_documents() -> dict[str, str]:
    upload_docs: dict[str, str] = {}
    for path in DOCS_DIR.glob("*"):
        if path.is_file() and path.suffix in {".txt", ".md"}:
            upload_docs[f"uploaded:{path.name}"] = path.read_text(encoding="utf-8")
    return upload_docs


def demo_repository_mode() -> None:
    repo_docs = load_repository_documents()
    collection = create_vector_store(repo_docs, "sample_repo", chunk_size=400, overlap_percent=10.0)
    results = search_vector_store(collection, "What does this sample project expose?", k=3)
    print("\nRepository mode results:")
    for hit in results:
        print(f"- {hit['file_path']} (similarity={hit['similarity']:.3f})")


def demo_document_mode() -> None:
    docs = load_uploaded_documents()
    collection = create_vector_store(docs, "sample_docs", chunk_size=400, overlap_percent=10.0)
    results = search_vector_store(collection, "What is an API status code?", k=2)
    print("\nDocument mode results:")
    for hit in results:
        print(f"- {hit['file_path']} (similarity={hit['similarity']:.3f})")


if __name__ == "__main__":
    demo_repository_mode()
    demo_document_mode()
    print()
    print("Sample run complete (OK)")
