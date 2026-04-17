import os
from dotenv import load_dotenv
import requests
import time
import json
from collections import defaultdict

load_dotenv()

session_token = os.getenv("LEETCODE_SESSION")
csrf_token = os.getenv("LEETCODE_CSRF_TOKEN")

# Configuring impersonation session
session = requests.Session()

# Injecting Cookies
session.cookies.set("LEETCODE_SESSION", session_token)
session.headers["X-CSRF-TOKEN"] = csrf_token

# Inject headers
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "x-csrftoken": csrf_token,
    "Referer": "https://leetcode.com/",
    "Content-Type": "application/json"
})


def fetch_user_submissions() -> dict[int, list[dict]]:
    return {}
    offset = 0
    limit = 20
    has_next = True

    accepted_submissions: dict[int, list[dict]] = defaultdict(list)

    while has_next:
        url = f"https://leetcode.com/api/submissions/?offset={offset}&limit={limit}"

        response = session.get(url)

        if response.status_code == 200:
            data = response.json()

            # LeetCode stores the actual list inside a key called 'submissions_dump'
            submissions = data.get("submissions_dump", [])

            if not submissions:
                print("Reached end of submissions")
                has_next = False
                break

            for submission in submissions:
                question_id = submission.get("question_id")
                status = submission.get("status_display")
                
                # We only want Accepted answers
                if status == "Accepted":
                    accepted_submissions[question_id].append({
                        "title": submission.get("title"),
                        "title_slug": submission.get("title_slug"), # URL friendly name
                        "lang": submission.get("lang"),
                        "runtime": submission.get("runtime"),
                        "memory": submission.get("memory"),
                        "code": submission.get("code"),
                        "timestamp": submission.get("timestamp")
                    })
            
            offset += limit
            time.sleep(5)  # Delay to prevent rate-limiting
            
        else:
            print(f"Error {response.status_code}: {response.text}")
            break

    return accepted_submissions

def dump_submissions(submissions: dict[int, list[dict]]) -> None:
    """Dump submissions to JSON file"""
    
    # Construct an absolute path relative to the script location
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    json_path = os.path.join(data_dir, "submissions_cache.json")
    
    # Create data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Read existing submissions if cache exists
    existing_submissions: dict[int, list[dict]] = {}
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            existing_submissions = json.load(f)
    
    # Merge
    for question_id, new_submissions in submissions.items():
        # JSON keys are always strings, so we convert the int question_id to a string
        q_id_str = str(question_id)
        if q_id_str in existing_submissions:
            existing_submissions[q_id_str].extend(new_submissions)
        else:
            existing_submissions[q_id_str] = new_submissions
            
        # Sort submissions by timestamp ascending (oldest first)
        existing_submissions[q_id_str].sort(key=lambda x: x.get("timestamp", 0))

    with open(json_path, "w") as f:
        json.dump(existing_submissions, f, indent=4)

    print("Cache saved successfully!")
    

def main():
    user_submissions = fetch_user_submissions()
    dump_submissions(user_submissions)

if __name__ == "__main__":
    main()