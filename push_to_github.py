"""
BEN Discord Bot - Direct GitHub Push Utility
Pushes all project files directly to GitHub using GitHub's Git Data REST API.
Does not require git.exe to be installed.
Guarantees .env and sensitive data are NEVER uploaded.
"""
import os
import sys
import base64
import json
import urllib.request
import urllib.error

REPO_OWNER = "kairogamingfl"
REPO_NAME = "BenBot"
BRANCH = "main"

# Files and directories to strictly ignore
IGNORED_PATTERNS = {
    ".env", ".venv", "venv", "__pycache__", ".git", "ben.db",
    "transcript", ".pyc"
}

def is_ignored(rel_path: str) -> bool:
    parts = rel_path.replace("\\", "/").split("/")
    for part in parts:
        if part in IGNORED_PATTERNS or part.endswith(".pyc") or part.endswith(".db"):
            return True
    return False

def make_request(url: str, token: str, data: dict = None, method: str = "GET") -> dict:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "BEN-Bot-Uploader/1.0"
    }
    encoded_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("message", err_body)
        except Exception:
            msg = err_body
        raise RuntimeError(f"GitHub API Error [{e.code}]: {msg}")

def collect_files(root_dir: str):
    files_to_upload = []
    for root, dirs, files in os.walk(root_dir):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, root_dir)
            if not is_ignored(rel_path):
                files_to_upload.append((rel_path, full_path))
    return files_to_upload

def push_repo(token: str, commit_message: str = "Initial commit: BEN Discord Bot with transparent UI"):
    base_api = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
    root_dir = os.path.dirname(os.path.abspath(__file__))

    print("==================================================")
    print(f" Pushing BEN Bot to https://github.com/{REPO_OWNER}/{REPO_NAME}")
    print("==================================================")

    # 1. Check repo access
    print("[1/5] Verifying repository access...")
    repo_info = make_request(base_api, token)
    default_branch = repo_info.get("default_branch", BRANCH)
    print(f"✔ Access verified for repository: {repo_info['full_name']} (Default branch: {default_branch})")

    # 2. Gather files & create blobs
    files = collect_files(root_dir)
    print(f"[2/5] Preparing {len(files)} files (Sensitive files like .env are strictly excluded)...")
    
    tree_items = []
    for rel_path, full_path in files:
        normalized_path = rel_path.replace("\\", "/")
        with open(full_path, "rb") as f:
            content_bytes = f.read()

        b64_content = base64.b64encode(content_bytes).decode("utf-8")
        blob_res = make_request(f"{base_api}/git/blobs", token, {
            "content": b64_content,
            "encoding": "base64"
        }, method="POST")

        tree_items.append({
            "path": normalized_path,
            "mode": "100644",
            "type": "blob",
            "sha": blob_res["sha"]
        })
        print(f"  + Uploaded: {normalized_path}")

    # 3. Create Tree
    print("[3/5] Creating Git Tree...")
    tree_res = make_request(f"{base_api}/git/trees", token, {"tree": tree_items}, method="POST")
    tree_sha = tree_res["sha"]

    # 4. Check for parent commit
    parent_sha = None
    ref_url = f"{base_api}/git/refs/heads/{default_branch}"
    try:
        ref_data = make_request(ref_url, token)
        parent_sha = ref_data["object"]["sha"]
    except Exception:
        pass

    # 5. Create Commit
    print("[4/5] Creating Git Commit...")
    commit_payload = {
        "message": commit_message,
        "tree": tree_sha,
        "parents": [parent_sha] if parent_sha else []
    }
    commit_res = make_request(f"{base_api}/git/commits", token, commit_payload, method="POST")
    new_commit_sha = commit_res["sha"]

    # 6. Update Reference
    print(f"[5/5] Updating branch '{default_branch}'...")
    if parent_sha:
        make_request(ref_url, token, {"sha": new_commit_sha, "force": True}, method="PATCH")
    else:
        make_request(f"{base_api}/git/refs", token, {
            "ref": f"refs/heads/{default_branch}",
            "sha": new_commit_sha
        }, method="POST")

    print("\n==================================================")
    print(" 🎉 SUCCESS! All files pushed to GitHub:")
    print(f" 👉 https://github.com/{REPO_OWNER}/{REPO_NAME}")
    print("==================================================")

if __name__ == "__main__":
    token = os.getenv("GITHUB_TOKEN")
    if not token and len(sys.argv) > 1:
        token = sys.argv[1]

    if not token:
        print("\nGitHub Personal Access Token is required to authenticate with GitHub.")
        token = input("Enter your GitHub Personal Access Token (PAT): ").strip()

    if not token:
        print("Error: No GitHub token provided.")
        sys.exit(1)

    try:
        push_repo(token)
    except Exception as e:
        print(f"\n[ERROR] Failed to push to GitHub: {e}")
        sys.exit(1)
