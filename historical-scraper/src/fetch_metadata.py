import os
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv()
session = requests.Session()
session.cookies.set("LEETCODE_SESSION", os.getenv("LEETCODE_SESSION"), domain="leetcode.com")
session.cookies.set("csrftoken", os.getenv("LEETCODE_CSRF_TOKEN"), domain="leetcode.com")

session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "x-csrftoken": os.getenv("LEETCODE_CSRF_TOKEN"),
    "Referer": "https://leetcode.com/",
    "Content-Type": "application/json"
})


def fetch_metadata(submissions: dict[str, dict[str, list[int]]]) -> None:
    """Fetch all submissions for a user"""
    
    # The GraphQL query structure
    graphql_url = "https://leetcode.com/graphql/"
    query = """
    query getQuestionDetail($titleSlug: String!) {
    question(titleSlug: $titleSlug) {
        difficulty
        topicTags {
        name
        }
    }
    }
    """

    updated_data = {}
    updated_data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "submissions_updated.json")

    # Load existing updated_data so we don't have to re-fetch metadata we already know
    if os.path.exists(updated_data_path):
        with open(updated_data_path, "r") as f:
            updated_data = json.load(f)

    for quest_id, sub_list in submissions.items():
        if not sub_list:
            continue
            
        title_slug = sub_list[0]["title_slug"]
        title = sub_list[0]["title"]

        # Clean up individual submissions
        clean_subs = []
        for sub in sub_list:
            clean_subs.append({
                "lang": sub.get("lang"),
                "runtime": sub.get("runtime"),
                "memory": sub.get("memory"),
                "code": sub.get("code"),
                "timestamp": sub.get("timestamp")
            })

        # Check if we already have the metadata cached
        if quest_id in updated_data:
            # We already know the difficulty and tags! 
            # We just need to update the submissions list with the newest cache
            updated_data[quest_id]["submissions"] = clean_subs
            print(f"Skipped API for {title_slug} (Loaded from cache)")
            continue
        
        # Build the GraphQL payload
        payload = {
            "query": query,
            "variables": {"titleSlug": title_slug}
        }
        
        response = session.post(graphql_url, json=payload)
        
        if response.status_code in [401, 403]:
            raise PermissionError("LeetCode Session cookie has expired or is invalid. Please update repository secrets.")

        elif response.status_code == 200:
            data = response.json()
            question_data = data.get("data", {}).get("question", {}) or {}
            
            difficulty = question_data.get("difficulty", "Unknown")
            raw_tags = question_data.get("topicTags", [])
            tags = [tag.get("name") for tag in raw_tags if tag]
            
            # Update our dictionary with the new structure
            updated_data[quest_id] = {
                "title": title,
                "title_slug": title_slug,
                "difficulty": difficulty,
                "tags": tags,
                "submissions": clean_subs
            }
            
            print(f"✅ Fetched metadata for {title_slug}")
            time.sleep(2)  # Polite delay to avoid GraphQL rate limits
        else:
            print(f"Error fetching {title_slug}: {response.status_code}")
            break

    with open(updated_data_path, "w") as f:
        json.dump(updated_data, f, indent=4)
    

def main() -> None:
    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "submissions_cache.json")
    
    with open(data_path, "r") as f:
        submissions = json.load(f)

    fetch_metadata(submissions)

if __name__ == "__main__":
    main()