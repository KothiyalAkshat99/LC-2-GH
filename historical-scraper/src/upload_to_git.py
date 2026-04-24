import os
import json
import subprocess
import requests
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_USER = os.environ.get("GITHUB_ID")

LANG_MAP = {
    "python3": ".py",
    "python": ".py",
    "java": ".java",
    "cpp": ".cpp",
    "javascript": ".js",
    "typescript": ".ts",
    "mysql": ".sql",
    "c": ".c",
    "csharp": ".cs"
}

# Helper function to run terminal commands safely in the repo directory
def run_git(args: list[str], root_dir: Path) -> None:
    subprocess.run(["git"] + args, cwd=root_dir, check=False, capture_output=True)


def create_remote_repo(repo_name: str) -> tuple[str, bool]:
    """Uses the GitHub REST API to create a new private repository if it doesn't already exist."""

    print(f"Checking remote GitHub repository '{repo_name}'...")

    url = "https://api.github.com/user/repos"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    payload = {
        "name": repo_name,
        "description": "Historical algorithm submissions synchronized via automated ETL pipeline.",
        "private": True,  # Keeping it private by default
        "auto_init": False # Crucial: We want an empty repo so we can push our local history to it
    }
    
    response = requests.post(url, headers=headers, json=payload)

    print(response.text)
    
    if response.status_code == 201:
        print("Successfully created remote repository on GitHub!")
        return (response.json().get("clone_url"), True)
    elif response.status_code == 422: # 422 means it already exists
        print("Remote repository already exists. We will push to it.")
        return (f"https://github.com/{GITHUB_USER}/{repo_name}.git", False)
    else:
        print(f"Failed to create remote repo. Status: {response.status_code}")
        print(response.json())
        exit(1)


def sync_repository(repo_name: str, remote_url: str, is_new_remote: bool) -> None:
    root_dir = Path(f"./{repo_name}")
    auth_remote_url = remote_url.replace("https://", f"https://{GITHUB_USER}:{GITHUB_TOKEN}@")
    
    # 1. Local Git Initialization / Synchronization
    if is_new_remote:
        print("New remote repository detected. Initializing local folder...")
        root_dir.mkdir(exist_ok=True)
        run_git(["init"], root_dir)
        run_git(["branch", "-M", "main"], root_dir)
        run_git(["remote", "add", "origin", auth_remote_url], root_dir)
    else:
        print("Existing remote repository detected.")
        if not root_dir.exists() or not (root_dir / ".git").exists():
            print("Local repository missing. Cloning from GitHub...")
            subprocess.run(["git", "clone", auth_remote_url, str(root_dir)], check=True)
        else:
            print("Local repository found. Pulling latest changes...")
            run_git(["remote", "set-url", "origin", auth_remote_url], root_dir)
            run_git(["pull", "origin", "main"], root_dir)
            
    # 2. Build local files (overwriting existing ones)
    print("Loading submissions and generating local files...")
    try:
        data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "submissions_updated.json")
        with open(data_path, "r") as f:
            cache = json.load(f)
    except FileNotFoundError:
        print("data/submissions_updated.json not found!")
        return
        
    for question_id, data in cache.items():
        difficulty = data.get("difficulty", "Unknown")
        subs = data.get("submissions", [])
        if not subs:
            continue
            
        latest_sub = subs[-1]
        primary_lang = latest_sub.get("lang", "python3")
        extension = LANG_MAP.get(primary_lang, ".txt")
        
        problem_dir = root_dir / difficulty
        problem_dir.mkdir(parents=True, exist_ok=True)
        
        padded_id = str(question_id).zfill(4)
        file_name = f"{padded_id}-{data.get('title_slug')}{extension}"
        file_path = problem_dir / file_name
        
        tags_str = ", ".join(data.get("tags", []))
        c_start = "/*\n" if extension in [".java", ".cpp", ".js", ".ts", ".c", ".cs"] else '"""\n'
        c_end   = "*/\n" if extension in [".java", ".cpp", ".js", ".ts", ".c", ".cs"] else '"""\n'
        
        file_content = [
            f"{c_start}",
            f"Problem Name: {data.get('title')}\n",
            f"Difficulty: {difficulty}\n",
            f"Tags: {tags_str}\n",
            f"{c_end}\n"
        ]
        
        for i, sub in enumerate(subs):
            sub_lang = sub.get("lang", "python3")
            runtime = sub.get("runtime", "N/A")
            memory = sub.get("memory", "N/A")
            
            file_content.append(f"{c_start}")
            file_content.append(f"Submission {i+1}\n")
            file_content.append(f"Language: {sub_lang}\n")
            file_content.append(f"Runtime: {runtime}\n")
            file_content.append(f"Memory: {memory}\n")
            file_content.append(f"{c_end}")
            file_content.append(sub.get("code", "") + "\n\n")
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("".join(file_content))
            
    print(f"Generated/Updated files locally.")
    
    # 3. Check for changes and push
    status_result = subprocess.run(["git", "status", "--porcelain"], cwd=root_dir, capture_output=True, text=True)
    if not status_result.stdout.strip():
        print("Everything is up to date! No new changes to push.")
        return
        
    print("Changes detected. Committing and pushing to GitHub...")
    run_git(["add", "."], root_dir)
    run_git(["commit", "-m", "Auto-sync new LeetCode submissions"], root_dir)
    
    push_result = subprocess.run(["git", "push", "-u", "origin", "main"], cwd=root_dir, capture_output=True, text=True)
    
    if push_result.returncode == 0:
        print("Success! All historical data is now live on GitHub.")
    else:
        print("Git Push Failed:")
        print(push_result.stderr)

def main():
    args = argparse.ArgumentParser()
    args.add_argument("--repo", type=str, required=True, help="Name of the remote repository")
    args = args.parse_args()

    remote_url, is_new_remote = create_remote_repo(args.repo)
    sync_repository(args.repo, remote_url, is_new_remote)

if __name__ == "__main__":
    main()