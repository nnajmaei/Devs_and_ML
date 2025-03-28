import os
import subprocess
from datetime import datetime, timedelta

# --- CONFIGURATION ---
REPO_PATH = "/Users/niman/Desktop/Pad/Work/Trajekt/ArcMachine"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = os.path.join(SCRIPT_DIR, "branches_list.txt")
DATE_FORMAT = "%Y-%m-%d %H:%M:%S %z"  # Git log --format=%ci format


def get_remote_branches_with_dates():
    """Returns a dictionary: {branch_name: last_commit_date}"""
    try:
        output = subprocess.check_output(
            ["git", "branch", "-r"], cwd=REPO_PATH, stderr=subprocess.DEVNULL
        )
        lines = output.decode("utf-8").splitlines()
        branches_with_dates = {}

        for line in lines:
            branch = line.strip()

            # Skip symbolic refs like 'origin/HEAD -> origin/main'
            if "->" in branch:
                continue

            try:
                date_output = subprocess.check_output(
                    ["git", "log", "-1", "--format=%ci", branch],
                    cwd=REPO_PATH,
                    stderr=subprocess.DEVNULL,
                )
                date_str = date_output.decode("utf-8").strip()
            except subprocess.CalledProcessError:
                date_str = "1970-01-01 00:00:00 +0000"  # fallback

            branches_with_dates[branch] = date_str
        return branches_with_dates
    except subprocess.CalledProcessError:
        print(f"❌ Error: Git not accessible in repo path: {REPO_PATH}")
        return {}


def read_saved_branches():
    """Reads the saved file and returns {branch_name: date_str}"""
    if not os.path.exists(FILE_NAME):
        return {}

    saved = {}
    with open(FILE_NAME, "r") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                date_str, branch_name = line.strip().split(" - ", 1)
                branch_name = branch_name.replace(" ****", "").strip()

                saved[branch_name.strip()] = date_str.strip()
            except ValueError:
                continue
    return saved


def save_branch_list(branches_with_dates):
    """Saves branch list with priority branches first, then the rest by latest date.
    Adds '****' to branches inactive for more than 3 months.
    """
    priority_order = [
        "origin/deploy/main",
        "origin/deploy/beta",
        "origin/deploy/staging",
        "origin/deploy/dev",
    ]
    priority_branches = []
    other_branches = []

    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, DATE_FORMAT)
        except Exception:
            return datetime.min

    two_months_ago = datetime.now().astimezone() - timedelta(days=60)

    for branch, date_str in branches_with_dates.items():
        if branch in priority_order:
            priority_branches.append((branch, date_str))
        else:
            other_branches.append((branch, date_str))

    # Sort the non-priority branches by date
    sorted_others = sorted(other_branches, key=lambda x: parse_date(x[1]), reverse=True)

    # Sort the priority branches by the defined order
    sorted_priority = sorted(
        priority_branches, key=lambda x: priority_order.index(x[0])
    )

    with open(FILE_NAME, "w") as f:
        for branch, date_str in sorted_priority + sorted_others:
            display_branch = branch
            if parse_date(date_str) < two_months_ago:
                display_branch += " ****"
            f.write(f"{date_str} - {display_branch}\n")


def main():
    saved = read_saved_branches()
    current = get_remote_branches_with_dates()

    saved_branches = set(saved.keys())
    current_branches = set(current.keys())

    new_branches = sorted(current_branches - saved_branches)
    deleted_branches = sorted(saved_branches - current_branches)
    unchanged_branches = sorted(current_branches & saved_branches)

    if new_branches:
        print("🟢 New remote branches:")
        for branch in new_branches:
            print(f" + [{current[branch]}] {branch}")
    else:
        print("✅ No new remote branches.")

    if deleted_branches:
        print("🔴 Deleted remote branches:")
        for branch in deleted_branches:
            print(f" - [{saved[branch]}] {branch}")
    else:
        print("✅ No deleted remote branches.")

    print(f"✅ Present remote branches: {len(unchanged_branches)}")
    save_branch_list(current)


if __name__ == "__main__":
    main()
