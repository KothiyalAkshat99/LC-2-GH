import subprocess
import argparse
import sys
import os

def run_step(command: list[str], step_name: str):
    print(f"\n{'='*50}")
    print(f"Starting Phase: {step_name}")
    print(f"{'='*50}")
    
    try:
        # We run the command natively so its output streams directly to the terminal
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\nPhase '{step_name}' failed with exit code {e.returncode}.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="LC-2-GH ETL Pipeline Orchestrator")
    parser.add_argument("--repo", type=str, required=True, help="Name of the remote GitHub repository")
    args = parser.parse_args()

    
    # Ensure we are running from the historical-scraper root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    try:
        # 1. Extract
        run_step([sys.executable, "src/LC_scraper.py"], "Extract (Scraping LeetCode)")
        
        # 2. Transform
        run_step([sys.executable, "src/fetch_metadata.py"], "Transform (Fetching Metadata)")
        
        # 3. Load
        run_step([sys.executable, "src/upload_to_git.py", "--repo", args.repo], "Load (Git Synchronization)")

        print(f"\nPipeline completed successfully! All data synced to '{args.repo}'.")

    except PermissionError as pe:
        print(f"\n==========================================")
        print(f"[CRITICAL ERROR] Authentication Failed!")
        print(pe)
        print(f"==========================================")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
