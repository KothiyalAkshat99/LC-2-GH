# Historical Scraper (LC-2-GH)

This folder contains the Python-based ETL (Extract, Transform, Load) tool used to scrape your historical problem submissions from LeetCode and synchronize them directly into a target GitHub repository. 

This serves as the "batch sync" component of the larger **LC-2-GH** project, ensuring that your past work is preserved before the browser extension takes over for real-time tracking.

---

## 🚀 Features
*   **Idempotent Synchronization:** Safely run the script as many times as you want. It uses Timestamp Watermarking and KV Caching to only fetch and commit *new* data.
*   **Authentication via Session Cookies:** Bypasses aggressive bot-detection systems (e.g., Cloudflare) by securely simulating your active browser session.
*   **Internal API Reverse Engineering:** Queries LeetCode's undocumented internal GraphQL and REST APIs to pull down your complete submission history, source code, problem metadata, tags, and difficulty ratings.
*   **Data Deduplication:** Merges multiple attempts at the same problem into a single file to keep your repository clean.
*   **Automated Git Sync:** Formats the files locally, initializes a Git repository, automatically provisions a private remote repository via GitHub's REST API, and pushes the history seamlessly.

---

## 🛠️ Architecture

The pipeline is split into three distinct modules located in the `src/` directory, managed by a central orchestrator:

1.  **Extract (`src/LC_scraper.py`)**: Paginates through your submission history. It uses a high-water mark to stop fetching if it sees submissions it has already processed. Saves state to `data/submissions_cache.json`.
2.  **Transform (`src/fetch_metadata.py`)**: Reads the cache and queries LeetCode's GraphQL API to discover the difficulty level and topic tags. It uses `data/submissions_updated.json` as a KV cache to avoid querying LeetCode for problems we already know the metadata for.
3.  **Load (`src/upload_to_git.py`)**: Reads the final transformed JSON, generates the local directory structure (organized by Difficulty), creates metadata templates in the code files, and orchestrates the Git push. It performs `git status` checks to skip commits if nothing changed.

---

## 💻 Setup & Usage

### 1. Install Dependencies
Ensure you have Python 3.8+ installed. Set up your virtual environment and install the required packages:
```bash
python -m venv .venv
.\.venv\Scripts\activate  # On Windows
# source .venv/bin/activate # On Mac/Linux
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in this directory (`historical-scraper/.env`). You will need to provide four keys:
```env
LEETCODE_SESSION=your_leetcode_session_cookie
LEETCODE_CSRF_TOKEN=your_csrf_token
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_ID=your_github_username
```

**How to get your LeetCode Cookies:**
1. Log into LeetCode on your browser.
2. Open Developer Tools (F12) -> Application tab (or Storage tab).
3. Under "Cookies" for `https://leetcode.com`, find `LEETCODE_SESSION` and `csrftoken`.
4. Copy their values into your `.env` file.

**How to get your GitHub Token:**
1. Go to GitHub -> Settings -> Developer Settings -> Personal Access Tokens (Classic).
2. Generate a new token with the `repo` scope enabled.

### 3. Run the Pipeline
You do not need to run the phases individually. Use the central orchestrator to run the entire ETL pipeline synchronously.

```bash
python main.py --repo Your-Target-Repo-Name
```
*(If the repository does not exist on your GitHub account, the script will automatically create a private one for you.)*

Because the pipeline is highly idempotent, it is completely safe to cancel it midway via `Ctrl+C`. The next time you run it, it will pick up exactly where it left off.
