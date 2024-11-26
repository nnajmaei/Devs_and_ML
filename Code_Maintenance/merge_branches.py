import os
import subprocess

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
            print(RED + "Invalid input. Please enter 'yes', 'y', 'no', or 'n'." + RESET)


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


def main():
    repo_path = "/Users/niman/Desktop/Pad/Work/Trajekt/ArcMachine/"
    os.chdir(repo_path)

    # Get the list of local branches
    stdout, stderr, returncode = run_git_command(["git", "branch"], repo_path)
    if returncode != 0:
        print(RED + f"Error listing branches: {stderr}" + RESET)
        return

    branches = [line.strip("* ").strip() for line in stdout.splitlines()]

    for branch in branches:
        print("\n" + "=" * 50)  # Separation line
        print(BOLD + f"Branch: {branch}" + RESET)
        print("=" * 50)

        if branch.startswith("deploy"):
            print(CYAN + f"Skipping deploy branch: {branch}" + RESET)
            continue

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
            print(
                RED
                + f"Warning: Unsupported branch pattern for {branch}. Skipping..."
                + RESET
            )
            continue

        # Check if a merge is needed
        print(CYAN + f"Checking if merge is needed for {branch}..." + RESET)
        if not check_if_merge_needed(branch, merge_from, repo_path):
            print(
                GREEN + f"No changes to merge for branch {branch}. Skipping..." + RESET
            )
            continue

        if not get_user_confirmation(
            "Do you want to merge this branch? (yes/y or no/n): "
        ):
            print(CYAN + "Skipping..." + RESET)
            continue

        # Checkout the branch
        print(CYAN + f"Checking out {branch}..." + RESET)
        _, stderr, returncode = run_git_command(["git", "checkout", branch], repo_path)
        if returncode != 0:
            print(RED + f"Error checking out branch {branch}: {stderr}" + RESET)
            continue

        # Merge
        print(CYAN + f"Merging from {merge_from} into {branch}..." + RESET)
        _, stderr, returncode = run_git_command(["git", "merge", merge_from], repo_path)
        if returncode != 0:
            print(RED + f"Merge conflict or error: {stderr}" + RESET)
            if not get_user_confirmation(
                "Do you want to resolve the conflicts? (yes/y or no/n): "
            ):
                print(YELLOW + "Aborting merge..." + RESET)
                run_git_command(["git", "merge", "--abort"], repo_path)
                continue
            print(CYAN + "Resolve the conflicts and press Enter when done." + RESET)
            input()

        # Commit the merge
        commit_message = f"merged in {merge_from}"
        stdout, stderr, returncode = run_git_command(
            ["git", "commit", "-am", commit_message], repo_path
        )
        if returncode != 0:
            if "nothing to commit" in stderr.lower():
                print(GREEN + f"No changes to commit for branch {branch}." + RESET)
            else:
                print(RED + f"Error committing merge: {stderr}" + RESET)
            continue

        # Push the changes
        print(CYAN + f"Pushing branch {branch}..." + RESET)
        _, stderr, returncode = run_git_command(["git", "push"], repo_path)
        if returncode != 0:
            print(RED + f"Error pushing branch {branch}: {stderr}" + RESET)


if __name__ == "__main__":
    main()
