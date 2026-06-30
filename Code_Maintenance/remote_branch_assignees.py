import os
import shutil
import subprocess
from datetime import datetime, timedelta

# --- CONFIGURATION ---
REPO_PATH = "/Users/niman/Desktop/Pad/Work/Trajekt/ArcMachine"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "remote_branch_assignees.txt")
DATE_FORMAT = "%Y-%m-%d %H:%M:%S %z"
OLD_BRANCH_DAYS = 60


def run_command(command):
    result = subprocess.run(
        command,
        cwd=REPO_PATH,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout, result.stderr, result.returncode


def parse_date(date_str):
    try:
        return datetime.strptime(date_str, DATE_FORMAT)
    except ValueError:
        return datetime.min.replace(tzinfo=datetime.now().astimezone().tzinfo)


def get_remote_branches():
    stdout, stderr, returncode = run_command(
        [
            "git",
            "for-each-ref",
            "--format=%(refname:short)|%(committerdate:iso8601)",
            "refs/remotes/origin",
        ]
    )
    if returncode != 0:
        raise RuntimeError(f"Error listing remote branches: {stderr.strip()}")

    branches = []
    for line in stdout.splitlines():
        if not line.strip() or "origin/HEAD" in line:
            continue

        branch, date_str = line.split("|", 1)
        branch = branch.strip()
        if branch == "origin":
            continue

        branches.append(
            {
                "remote_branch": branch,
                "local_branch": branch.removeprefix("origin/").strip(),
                "date_str": date_str.strip(),
                "date": parse_date(date_str.strip()),
            }
        )

    return sorted(branches, key=lambda item: item["date"], reverse=True)


def gh_available():
    if not shutil.which("gh"):
        return False

    _, _, returncode = run_command(["gh", "auth", "status"])
    return returncode == 0


def get_pr_assignees(local_branch):
    stdout, _, returncode = run_command(
        [
            "gh",
            "pr",
            "list",
            "--head",
            local_branch,
            "--state",
            "open",
            "--json",
            "assignees",
            "--jq",
            ".[].assignees[].login",
        ]
    )
    if returncode != 0:
        return []

    return sorted({line.strip() for line in stdout.splitlines() if line.strip()})


def build_report():
    branches = get_remote_branches()
    can_check_assignees = gh_available()
    old_cutoff = datetime.now().astimezone() - timedelta(days=OLD_BRANCH_DAYS)

    lines = []
    lines.append("# Remote Branch Assignees")
    lines.append(f"# Generated from: {REPO_PATH}")
    lines.append("# Format: last commit date - remote branch - assignee(s)")
    lines.append("# * means no assignee and last commit is older than 60 days")
    if not can_check_assignees:
        lines.append("# Warning: gh is unavailable or unauthenticated; assignees show as none")
    lines.append("")

    for branch in branches:
        assignees = get_pr_assignees(branch["local_branch"]) if can_check_assignees else []
        assignee_text = ", ".join(assignees) if assignees else "none"
        marker = " *" if not assignees and branch["date"] < old_cutoff else ""
        lines.append(
            f"{branch['date_str']} - {branch['remote_branch']}{marker} - {assignee_text}"
        )

    return "\n".join(lines) + "\n"


def main():
    report = build_report()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        file.write(report)

    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
