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

def create_remote_repo(repo_name):
    """Uses the GitHub REST API to create a new private repository."""

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
    
    if response.status_code == 201:
        print("Successfully created remote repository on GitHub!")
        return response.json().get("clone_url")
    elif response.status_code == 422: # 422 means it already exists
        print("Remote repository already exists. We will push to it.")
        return f"https://github.com/{GITHUB_USER}/{repo_name}.git"
    else:
        print(f"Failed to create remote repo. Status: {response.status_code}")
        print(response.json())
        exit(1)


def build_and_push(repo_name):
    print("Loading submissions...")
    
    try:
        data_path = os.path.join(os.path.dirname(__file__), "data", "submissions_updated.json")
        with open(data_path, "r") as f:
            cache = json.load(f)
    except FileNotFoundError:
        print("data/submissions_updated.json not found!")
        return

    # 1. Create the Local File Structure
    root_dir = Path(f"./{repo_name}")
    root_dir.mkdir(exist_ok=True)
    
    print("Generating local files...")
    for question_id, data in cache.items():
        difficulty = data.get("difficulty", "Unknown")
        
        subs = data.get("submissions", [])
        if not subs:
            continue
            
        # We'll use the language of the latest submission to determine the file extension
        latest_sub = subs[-1]
        primary_lang = latest_sub.get("lang", "python3")
        extension = LANG_MAP.get(primary_lang, ".txt")
        
        # Create directory path: e.g., algorithm-submissions/Easy/
        problem_dir = root_dir / difficulty
        problem_dir.mkdir(parents=True, exist_ok=True)
        
        # Format filename: e.g., 0001-two-sum.py
        padded_id = str(question_id).zfill(4)
        file_name = f"{padded_id}-{data.get('title_slug')}{extension}"
        file_path = problem_dir / file_name
        
        tags_str = ", ".join(data.get("tags", []))
        
        c_start = "/*\n" if extension in [".java", ".cpp", ".js", ".ts", ".c", ".cs"] else '"""\n'
        c_end   = "*/\n" if extension in [".java", ".cpp", ".js", ".ts", ".c", ".cs"] else '"""\n'
        
        # Build the top-level metadata
        file_content = [
            f"{c_start}",
            f"Problem Name: {data.get('title')}\n",
            f"Difficulty: {difficulty}\n",
            f"Tags: {tags_str}\n",
            f"{c_end}\n"
        ]
        
        # Append every submission to the file
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
            
        # Write the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("".join(file_content))

    print(f"Generated {len(cache)} files locally.")

    # 2. Create the Remote Repository
    remote_url = create_remote_repo(repo_name)
    
    # 3. Local Git Orchestration & Push
    print("Executing Git commands...")
    
    # Helper function to run terminal commands safely in the repo directory
    def run_git(args):
        subprocess.run(["git"] + args, cwd=root_dir, check=False, capture_output=True)

    run_git(["init"])
    run_git(["branch", "-M", "main"])
    run_git(["add", "."])
    run_git(["commit", "-m", "Initial bulk sync of historical submissions"])
    
    # Remove origin if it exists to avoid errors, then add the fresh one
    run_git(["remote", "remove", "origin"]) 
    
    # Inject the PAT directly into the URL for a passwordless push
    auth_remote_url = remote_url.replace("https://", f"https://{GITHUB_USER}:{GITHUB_TOKEN}@")
    run_git(["remote", "add", "origin", auth_remote_url])
    
    print("Pushing to GitHub (this may take a few seconds)...")
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
    
    build_and_push(args.repo)


if __name__ == "__main__":
    main()