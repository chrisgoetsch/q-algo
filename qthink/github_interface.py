# File: qthink/github_interface.py

from github import Github
import os
from dotenv import load_dotenv

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_API_TOKEN")
REPO_NAME = os.getenv("REPO_NAME", "chrisgoetsch/q-algo")

def get_open_pr_titles():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    return [pr.title for pr in repo.get_pulls(state="open")]

def get_recent_commit_summaries(limit=5):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    commits = repo.get_commits()
    return [commit.commit.message.strip().split("\n")[0] for commit in commits[:limit]]

def get_latest_open_pr_number():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    pulls = repo.get_pulls(state="open", sort="updated", direction="desc")
    pr = next(iter(pulls), None)  # ✅ Fix: wrap with iter()
    return pr.number if pr else None


def get_pr_file_diffs(pr_number, max_chars_per_file=1000):
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    pr = repo.get_pull(pr_number)
    files = pr.get_files()
    return {
        f.filename: f.patch[:max_chars_per_file]  # Trim long patches
        for f in files if hasattr(f, 'patch') and f.patch
    }
