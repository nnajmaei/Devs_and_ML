import os
import subprocess
import sys

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
DEPLOY_BRANCHES = ["deploy/main", "deploy/beta", "deploy/staging", "deploy/dev"]
PR_ASSIGNEE_TO_MERGE = "nnajmaei"


def run_git_command(command, cwd):
    """Run a git command in the specified directory."""
    try:
        result = subprocess.run(
            command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1


def get_current_branch(repo_path):
    """Retrieve the current git branch."""
    stdout, stderr, returncode = run_git_command(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], repo_path
    )
    if returncode == 0:
        return stdout.strip()
    else:
        print(RED + f"Error retrieving current branch: {stderr}" + RESET)
        sys.exit(1)


def pull_recursively(repo_path):
    """Pull the latest changes recursively for the current branch."""
    print(CYAN + "Pulling recursively..." + RESET)
    stdout, stderr, returncode = run_git_command(
        ["git", "pull", "--recurse-submodules"], repo_path
    )
    if returncode != 0:
        print(RED + f"Error pulling changes: {stderr}" + RESET)
        return False
    return True


def get_user_confirmation(prompt):
    """Prompt the user for a yes/no confirmation."""
    while True:
        response = input(CYAN + prompt + RESET).strip().lower()
        if response in {"yes", "y"}:
            return True
        if response in {"no", "n"}:
            return False


def check_if_merge_needed(branch, merge_from, repo_path):
    """Check if there is anything to merge from the specified branch."""
    stdout, stderr, returncode = run_git_command(["git", "fetch", "origin"], repo_path)
    if returncode != 0:
        print(RED + f"Error fetching updates: {stderr}" + RESET)
        return False

    stdout, stderr, returncode = run_git_command(
        ["git", "log", f"{branch}..{merge_from}"], repo_path
    )
    if returncode != 0:
        print(RED + f"Error checking merge status: {stderr}" + RESET)
        return False

    return bool(stdout.strip())


def get_pr_assignees(branch, repo_path):
    """Return open GitHub PR assignees for a branch."""
    stdout, stderr, returncode = run_git_command(
        [
            "gh",
            "pr",
            "list",
            "--head",
            branch,
            "--state",
            "open",
            "--json",
            "assignees",
            "--jq",
            ".[].assignees[].login",
        ],
        repo_path,
    )
    if returncode != 0:
        print(
            YELLOW
            + f"Could not check PR assignees for {branch}: {stderr.strip()}"
            + RESET
        )
        return []

    return [line.strip() for line in stdout.splitlines() if line.strip()]


def branch_pr_assigned_to_user(branch, repo_path):
    """Check whether the branch's open PR is assigned to the configured user."""
    assignees = get_pr_assignees(branch, repo_path)
    if PR_ASSIGNEE_TO_MERGE in assignees:
        print(GREEN + f"PR assignee matched: {PR_ASSIGNEE_TO_MERGE}" + RESET)
        return True

    if assignees:
        print(
            YELLOW
            + f"PR assignee is not {PR_ASSIGNEE_TO_MERGE}: {', '.join(assignees)}"
            + RESET
        )
    else:
        print(YELLOW + "No open PR assignee found." + RESET)

    return False


def handle_merge_error():
    """Handle a merge error by prompting the user for action."""
    while True:
        response = input(
            YELLOW + "Merge error occurred. Do you want to:\n"
            "1. Continue to the next branch\n"
            "2. Cancel the whole process and exit\n"
            "Enter 1 or 2: " + RESET
        ).strip()
        if response == "1":
            return True
        if response == "2":
            print(RED + "Exiting the process." + RESET)
            sys.exit(1)

        print(RED + "Invalid input. Please enter 1 or 2." + RESET)


def merge_from_branch(branch, merge_from, repo_path):
    """Pull, merge, commit, and push a maintenance branch."""
    print(CYAN + f"Checking if merge is needed from {merge_from}..." + RESET)
    if not check_if_merge_needed(branch, merge_from, repo_path):
        print(GREEN + "No changes to merge. Skipping..." + RESET)
        return

    if not get_user_confirmation(
        f"Do you want to merge this branch with {merge_from}? (yes/y or no/n): "
    ):
        print(CYAN + "\nSkipping..." + RESET)
        return

    print(CYAN + f"Checking out..." + RESET)
    _, stderr, returncode = run_git_command(["git", "checkout", branch], repo_path)
    if returncode != 0:
        print(RED + f"Error checking out branch {branch}: {stderr}" + RESET)
        return

    if not pull_recursively(repo_path):
        return

    print(CYAN + f"Merging from {merge_from}..." + RESET)
    _, stderr, returncode = run_git_command(["git", "merge", merge_from], repo_path)
    if returncode != 0:
        print(RED + f"Merge conflict or error: {stderr}" + RESET)
        if not handle_merge_error():
            return
    else:
        print(GREEN + "Merge successful." + RESET)

    commit_message = f"merged in {merge_from}"
    _, stderr, returncode = run_git_command(
        ["git", "commit", "-am", commit_message], repo_path
    )
    if returncode != 0 and "nothing to commit" in stderr.lower():
        print(GREEN + f"No changes to commit for branch {branch}." + RESET)

    print(CYAN + "Pushing branch..." + RESET)
    _, stderr, returncode = run_git_command(["git", "push"], repo_path)
    if returncode != 0:
        print(RED + f"Error pushing branch: {stderr}" + RESET)
        handle_merge_error()


def main():
    repo_path = "/Users/niman/Desktop/Pad/Work/Trajekt/ArcMachine/"
    os.chdir(repo_path)

    # Capture the current branch
    original_branch = get_current_branch(repo_path)

    stdout, stderr, returncode = run_git_command(["git", "branch"], repo_path)
    if returncode != 0:
        print(RED + f"Error listing branches: {stderr}" + RESET)
        return

    branches = [line.strip("* ").strip() for line in stdout.splitlines()]
    priority_branches = DEPLOY_BRANCHES
    remaining_branches = [b for b in branches if b not in priority_branches]
    branches = priority_branches + remaining_branches

    for branch in branches:
        print("\n" + "=" * 50)  # Separation line
        print(BOLD + f"Branch: {branch}" + RESET)
        print("=" * 50)

        if branch in DEPLOY_BRANCHES:
            print(CYAN + f"Checking out..." + RESET)
            _, stderr, returncode = run_git_command(
                ["git", "checkout", branch], repo_path
            )
            if returncode != 0:
                print(RED + f"Error checking out branch {branch}: {stderr}" + RESET)
                continue

            pull_recursively(repo_path)
            continue

        if branch.startswith("dev/"):
            if branch_pr_assigned_to_user(branch, repo_path):
                merge_from_branch(branch, "origin/deploy/dev", repo_path)
            else:
                print(YELLOW + "Skipping because PR is not assigned to nnajmaei." + RESET)
            continue

        if branch.startswith("staging/"):
            if branch_pr_assigned_to_user(branch, repo_path):
                merge_from_branch(branch, "origin/deploy/staging", repo_path)
            else:
                print(YELLOW + "Skipping because PR is not assigned to nnajmaei." + RESET)
            continue

        if branch.startswith("beta/"):
            if branch_pr_assigned_to_user(branch, repo_path):
                merge_from_branch(branch, "origin/deploy/beta", repo_path)
            else:
                print(YELLOW + "Skipping because PR is not assigned to nnajmaei." + RESET)
            continue

        if branch.startswith("main/"):
            if branch_pr_assigned_to_user(branch, repo_path):
                merge_from_branch(branch, "origin/deploy/main", repo_path)
            else:
                print(YELLOW + "Skipping because PR is not assigned to nnajmaei." + RESET)
            continue

        print(YELLOW + "Skipping without pull or merge." + RESET)

    # Switch back to original branch
    print(CYAN + f"Switching back to original branch: {original_branch}" + RESET)
    _, stderr, returncode = run_git_command(
        ["git", "checkout", original_branch], repo_path
    )


if __name__ == "__main__":
    main()
