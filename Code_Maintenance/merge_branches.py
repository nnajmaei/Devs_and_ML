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


def run_git_command(command, cwd):
    """Run a git command in the specified directory."""
    try:
        result = subprocess.run(
            command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1


def get_user_confirmation(prompt):
    """Prompt the user for a yes/no confirmation."""
    while True:
        response = input(CYAN + prompt + RESET).strip().lower()
        if response in {"yes", "y"}:
            return True
        elif response in {"no", "n"}:
            return False
        else:
            print(RED + "Invalid input. Please enter 'yes' or 'no'." + RESET)


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

    return bool(stdout.strip())  # If there are logs, a merge is needed


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
            return True  # Continue to the next branch
        elif response == "2":
            print(RED + "Exiting the process." + RESET)
            sys.exit(1)
        else:
            print(RED + "Invalid input. Please enter 1 or 2." + RESET)


def reset_submodule_changes(submodule_path, repo_path):
    """Reset any changes made to the submodule."""
    print(YELLOW + f"Checking for changes in {submodule_path}..." + RESET)
    stdout, stderr, returncode = run_git_command(
        ["git", "status", "--porcelain", submodule_path], repo_path
    )
    if returncode != 0:
        print(RED + f"Error checking submodule status: {stderr}" + RESET)
        return False

    if stdout.strip():  # If there are changes
        print(YELLOW + f"Resetting changes in {submodule_path}..." + RESET)
        _, stderr, returncode = run_git_command(
            ["git", "reset", "--hard", submodule_path], repo_path
        )
        if returncode != 0:
            print(RED + f"Error resetting submodule changes: {stderr}" + RESET)
            return False

    return True


def main():
    repo_path = "/Users/niman/Desktop/Pad/Work/Trajekt/ArcMachine/"
    submodule_to_exclude = "core_utils/"
    os.chdir(repo_path)

    # Get the list of local branches
    stdout, stderr, returncode = run_git_command(["git", "branch"], repo_path)
    if returncode != 0:
        print(RED + f"Error listing branches: {stderr}" + RESET)
        return

    branches = [line.strip("* ").strip() for line in stdout.splitlines()]

    for branch in branches:
        if branch.startswith("deploy"):
            continue

        print("\n" + "=" * 50)  # Separation line
        print(BOLD + f"Branch: {branch}" + RESET)
        print("=" * 50)

        # Determine the correct branch to merge from
        if branch.startswith("dev/"):
            merge_from = "origin/deploy/dev"
        elif branch.startswith("staging/"):
            merge_from = "origin/deploy/staging"
        elif branch.startswith("beta/"):
            merge_from = "origin/deploy/beta"
        elif branch.startswith("main/"):
            merge_from = "origin/deploy/main"
        else:
            print(RED + f"Unsupported branch pattern.\nSkipping..." + RESET)
            continue

        # Check if a merge is needed
        print(CYAN + f"Checking if merge is needed..." + RESET)
        if not check_if_merge_needed(branch, merge_from, repo_path):
            print(GREEN + f"No changes to merge. \nSkipping..." + RESET)
            continue

        if not get_user_confirmation(
            "Do you want to merge this branch? (yes/y or no/n): "
        ):
            print(CYAN + "\nSkipping..." + RESET)
            continue

        # Checkout the branch
        print(CYAN + f"Checking out..." + RESET)
        _, stderr, returncode = run_git_command(["git", "checkout", branch], repo_path)
        if returncode != 0:
            print(RED + f"Error checking out branch {branch}: {stderr}" + RESET)
            continue

        # Merge
        print(CYAN + f"Merging from {merge_from}..." + RESET)
        stdout, stderr, returncode = run_git_command(
            ["git", "merge", merge_from], repo_path
        )
        if returncode != 0:
            print(RED + f"Merge conflict or error: {stderr}" + RESET)
            if not handle_merge_error():
                continue
        else:
            print(GREEN + f"Merge successful." + RESET)

        # Reset any submodule changes
        if not reset_submodule_changes(submodule_to_exclude, repo_path):
            print(RED + f"Skipping commit due to submodule reset failure." + RESET)
            continue

        # Commit the merge
        commit_message = f"merged in {merge_from} without {submodule_to_exclude}"
        stdout, stderr, returncode = run_git_command(
            ["git", "commit", "-am", commit_message], repo_path
        )
        if returncode != 0:
            if "nothing to commit" in stderr.lower():
                print(GREEN + f"No changes to commit for branch {branch}." + RESET)

        # Push the changes
        print(CYAN + f"Pushing branch..." + RESET)
        _, stderr, returncode = run_git_command(["git", "push"], repo_path)
        if returncode != 0:
            print(RED + f"Error pushing branch: {stderr}" + RESET)
            if not handle_merge_error():
                continue


if __name__ == "__main__":
    main()
