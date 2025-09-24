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

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--space-id", required=True, help="<org-or-user>/<space-name>")
    p.add_argument("--folder", default=".", help="Folder to upload (default: repo root)")
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
