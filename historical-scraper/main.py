import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

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


def fetch_user_submissions():
    url = "https://leetcode.com/api/submissions/?offset=0&limit=20"

    response = session.get(url)

    if response.status_code == 200:
        data = response.json()

        # LeetCode stores the actual list inside a key called 'submissions_dump'
        submissions = data.get("submissions_dump", [])

        for submission in submissions:
            if submission.get("status_display") == "Accepted":
                print(f"\n✅ Success! Found an accepted submission.")
                print(f"Problem:  {submission.get('title')}")
                print(f"Language: {submission.get('lang')}")
                print(f"Runtime:  {submission.get('runtime')}")
                print(f"\nCode Snippet:\n{'-'*30}\n{submission.get('code')[:200]}...\n{'-'*30}")
        
        print("\nNo 'Accepted' submissions found in the last 20 attempts.")
    
    elif response.status_code == 401 or response.status_code == 403:
        print("❌ Authentication failed. Your LEETCODE_SESSION token might be expired.")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        

def main():
    fetch_user_submissions()

if __name__ == "__main__":
    main()