"""
Push current repository contents to a Hugging Face Space using the Hugging Face Hub API.
Avoids git credential issues by using the token from the HF_TOKEN environment variable.

Usage (PowerShell):
  $env:HF_TOKEN = "<your token>"
  python scripts/push_to_hf.py --space-id mwill-AImission/github-guidebot-mvp

Notes:
- Requires huggingface-hub package.
- Ignores common local/CI artifacts (.git, .venv, __pycache__, artifacts, .pytest_cache).
- Creates the Space if it doesn't exist with SDK "docker".
"""
from __future__ import annotations
import argparse
import os
import sys
from huggingface_hub import HfApi, create_repo, hf_hub_url
import fnmatch
from pathlib import Path
from huggingface_hub.utils import HfHubHTTPError

DEFAULT_IGNORE = [
    ".git/*",
    ".venv/*",
    "__pycache__/*",
    ".pytest_cache/*",
    "artifacts/*",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".coverage",
    "*.ipynb_checkpoints/*",
]

PROTECTED_REMOTE = {".gitattributes", "README.md", "HF_README.md"}

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--space-id", required=True, help="<org-or-user>/<space-name>")
    p.add_argument("--folder", default=".", help="Folder to upload (default: repo root)")
    p.add_argument("--no-prune", action="store_true", help="Do not delete remote-only files.")
    args = p.parse_args()

    token = os.environ.get("HF_TOKEN")
    if not token:
        print("HF_TOKEN environment variable is not set.", file=sys.stderr)
        return 2

    api = HfApi()

    # Validate token
    try:
        who = api.whoami(token=token)
        # Don't print the token; just identity confirmation
        print(f"Authenticated to HF Hub as: {who.get('name') or who.get('username')}")
    except Exception as e:
        print(f"Authentication failed: {e}", file=sys.stderr)
        return 2

    # Ensure space exists
    try:
        api.repo_info(repo_id=args.space_id, repo_type="space", token=token)
        print(f"Space exists: {args.space_id}")
    except HfHubHTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            print(f"Creating Space {args.space_id} (sdk=docker)...")
            create_repo(
                repo_id=args.space_id,
                repo_type="space",
                space_sdk="docker",
                exist_ok=True,
                token=token,
            )
        else:
            print(f"Failed to check/create space: {e}", file=sys.stderr)
            return 2

    # Optionally prune remote-only files so Space mirrors local folder
    if not args.no_prune:
        print("Computing remote-only files to prune…")
        try:
            remote_files = set(api.list_repo_files(repo_id=args.space_id, repo_type="space", token=token))
        except Exception as e:
            print(f"Warning: could not list remote files: {e}")
            remote_files = set()

        # Build local file set applying ignore patterns
        root = Path(args.folder).resolve()
        local_paths: set[str] = set()
        for p in root.rglob('*'):
            if p.is_file():
                rel = p.relative_to(root).as_posix()
                # Skip ignored
                if any(fnmatch.fnmatch(rel, pat) for pat in DEFAULT_IGNORE):
                    continue
                local_paths.add(rel)

        # Anything remote that's not in local_paths should be deleted (except protected)
        to_delete = [rf for rf in remote_files if rf not in local_paths and rf not in PROTECTED_REMOTE]
        if to_delete:
            print(f"Pruning {len(to_delete)} remote file(s)…")
            for rf in to_delete:
                try:
                    api.delete_file(path=rf, repo_id=args.space_id, repo_type="space", token=token, commit_message=f"prune: remove stale {rf}")
                    print(f" - deleted {rf}")
                except Exception as e:
                    print(f" ! failed to delete {rf}: {e}")
        else:
            print("No remote-only files to prune.")

    # Upload folder
    print("Uploading repository contents (filtered)…")
    api.upload_folder(
        folder_path=args.folder,
        repo_id=args.space_id,
        repo_type="space",
        token=token,
        commit_message="sync: upload repository contents",
        ignore_patterns=DEFAULT_IGNORE,
    )
    space_url = f"https://huggingface.co/spaces/{args.space_id}"
    print(f"Upload complete. Space: {space_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
