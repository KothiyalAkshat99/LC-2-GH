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

    for quest_id, sub_list in submissions.items():
        if not sub_list:
            continue
            
        title_slug = sub_list[0]["title_slug"]
        title = sub_list[0]["title"]
        
        # Build the GraphQL payload
        payload = {
            "query": query,
            "variables": {"titleSlug": title_slug}
        }
        
        response = session.post(graphql_url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            question_data = data.get("data", {}).get("question", {}) or {}
            
            # Extract difficulty and format tags into a clean list of strings
            difficulty = question_data.get("difficulty", "Unknown")
            raw_tags = question_data.get("topicTags", [])
            tags = [tag.get("name") for tag in raw_tags if tag]
            
            # Clean up individual submissions (remove title/title_slug as they are now metadata)
            clean_subs = []
            for sub in sub_list:
                clean_subs.append({
                    "lang": sub.get("lang"),
                    "runtime": sub.get("runtime"),
                    "memory": sub.get("memory"),
                    "code": sub.get("code"),
                    "timestamp": sub.get("timestamp")
                })
            
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

    with open("data/submissions_updated.json", "w") as f:
        json.dump(updated_data, f, indent=4)


def main() -> None:
    data_path = "data/submissions_cache.json"
    
    with open(data_path, "r") as f:
        submissions = json.load(f)

    fetch_metadata(submissions)

if __name__ == "__main__":
    main()