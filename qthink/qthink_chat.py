import sys
from qthink_engine import ask_qthink
from github_interface import get_open_pr_titles, get_recent_commit_summaries

# Preload GitHub PR and commit context
try:
    open_prs = get_open_pr_titles()
    commit_summaries = get_recent_commit_summaries(limit=5)
    if open_prs:
        print("\n📂 Connected to GitHub repo. Open PRs:")
        for pr in open_prs:
            print(f"  - {pr}")
    else:
        print("\n📂 Connected to GitHub repo. No open PRs found.")
except Exception as e:
    print(f"\n⚠️ GitHub connection failed: {e}")
    open_prs = []
    commit_summaries = []

print("\n💬 QThink Assistant Ready — Type 'exit' to quit.\n")
while True:
    user_input = input("You: ")
    if user_input.lower() in ("exit", "quit"): break

    # Build contextual metadata for GPT
    pr_context = "\n".join(f"- {title}" for title in open_prs)
    commit_context = "\n".join(f"- {msg}" for msg in commit_summaries)

    context_message = (
        f"Open PRs:\n{pr_context}\n\nRecent Commits:\n{commit_context}\n\n"
        f"User question: {user_input}"
    )

    response = ask_qthink(context_message)
    print("QThink:", response)
