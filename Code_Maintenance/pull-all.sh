#!/bin/bash

# ANSI color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

if [ -z "$BASH_VERSION" ]; then
    exec /bin/bash "$0" "$@"
fi

cleanup_temp_copy() {
    if [ -n "$PULL_ALL_TEMP_COPY" ] && [ -f "$PULL_ALL_TEMP_COPY" ]; then
        rm -f "$PULL_ALL_TEMP_COPY"
    fi
}

# This script checks out multiple branches. Run from a temp copy so changing
# branches cannot swap out the script file while Bash is still reading it.
if [ -z "$PULL_ALL_RUNNING_FROM_COPY" ]; then
    SCRIPT_SOURCE="${BASH_SOURCE[0]}"
    if [[ "$SCRIPT_SOURCE" != /* ]]; then
        SCRIPT_SOURCE="$(pwd -P)/$SCRIPT_SOURCE"
    fi

    SCRIPT_COPY="$(mktemp /tmp/pull-all.XXXXXX.sh)"
    cp "$SCRIPT_SOURCE" "$SCRIPT_COPY"
    chmod +x "$SCRIPT_COPY"
    PULL_ALL_RUNNING_FROM_COPY=1 PULL_ALL_TEMP_COPY="$SCRIPT_COPY" exec /bin/bash "$SCRIPT_COPY" "$@"
fi

# Variables to track successful and failed pulls
SUCCESSFUL_PULLS=0
FAILED_PULLS=0
NO_CHANGES=0
DELETED_BRANCHES=0

# Arrays to store branch names
SUCCESSFUL_BRANCHES=()
FAILED_BRANCHES=()
NO_CHANGES_BRANCHES=()
DELETED_BRANCHES_LIST=()

# Branches that should be actively pulled.
should_pull_branch() {
    case "$1" in
        deploy/main|deploy/staging|deploy/beta|deploy/dev|deploy/rollback)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Non-deploy branches are pulled only when their open GitHub PR is assigned to
# one of these users. Requires the GitHub CLI to be installed and authenticated.
ASSIGNEES_TO_PULL=(
    "nnajmaei"
    "mat-trajekt"
    "sheikh-nooruddin"
    "ryanallen-traj"
    "justinmende"
)
ASSIGNEE_CHECK_AVAILABLE=1
BRANCH_PULL_ASSIGNEES=""
if ! command -v gh > /dev/null 2>&1; then
    ASSIGNEE_CHECK_AVAILABLE=0
    echo -e "${YELLOW}Warning: gh CLI not found. Only deploy branches will be pulled.${NC}"
elif ! gh auth status > /dev/null 2>&1; then
    ASSIGNEE_CHECK_AVAILABLE=0
    echo -e "${YELLOW}Warning: gh CLI is not authenticated. Only deploy branches will be pulled.${NC}"
fi

assignee_is_allowed() {
    local candidate="$1"
    local assignee

    for assignee in "${ASSIGNEES_TO_PULL[@]}"; do
        if [ "$candidate" == "$assignee" ]; then
            return 0
        fi
    done

    return 1
}

append_matching_assignee() {
    local assignee="$1"

    case ",$BRANCH_PULL_ASSIGNEES," in
        *",$assignee,"*)
            return
            ;;
    esac

    if [ -z "$BRANCH_PULL_ASSIGNEES" ]; then
        BRANCH_PULL_ASSIGNEES="$assignee"
    else
        BRANCH_PULL_ASSIGNEES="$BRANCH_PULL_ASSIGNEES, $assignee"
    fi
}

branch_assigned_to_user() {
    local branch="$1"
    local assignee

    if [ "$ASSIGNEE_CHECK_AVAILABLE" -ne 1 ]; then
        return 1
    fi

    BRANCH_PULL_ASSIGNEES=""
    while IFS= read -r assignee; do
        if assignee_is_allowed "$assignee"; then
            append_matching_assignee "$assignee"
        fi
    done < <(gh pr list \
        --head "$branch" \
        --state open \
        --json assignees \
        --jq '.[].assignees[].login' 2> /dev/null)

    if [ -n "$BRANCH_PULL_ASSIGNEES" ]; then
        return 0
    else
        return 1
    fi
}

# Save current directory (the one the script was *called* from)
REPO_ROOT="$(pwd -P)"

# Ensure we’re inside a git repo
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo -e "${RED}Error: This script must be run inside a Git repository.${NC}"
    exit 1
fi

# Store the current branch
ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Fetch the latest changes and prune remote branches in the repository directory
git fetch --all --prune
git remote prune origin

# Trap to ensure we return to the original branch before exit
trap 'cd "$REPO_ROOT" && git checkout "$ORIGINAL_BRANCH"; cleanup_temp_copy' EXIT

# Find all git repositories recursively
while IFS= read -r -d '' git_dir; do
    # Navigate to the parent directory of the .git directory
    repo_dir="$(cd "$(dirname "$git_dir")" && pwd -P)"
    # Only operate on the repo where the script was invoked.
    if [ "$repo_dir" != "$REPO_ROOT" ]; then
        continue
    fi
    # Navigate into the repository directory
    cd "$repo_dir" || continue
    
    # Store the current branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    
    # NEW: Ensure all remote branches (on origin) have local copies
    while IFS= read -r remote_branch; do
        # Trim leading spaces from remote branch names
        # and skip symbolic refs like "origin/HEAD -> origin/main"
        if [[ "$remote_branch" == *"->"* ]]; then
            continue
        fi
        
        # Only consider origin/* branches
        case "$remote_branch" in
            origin/*)
                local_branch="${remote_branch#origin/}"
                # If the local branch doesn't exist, create it tracking the remote
                if ! git show-ref --verify --quiet "refs/heads/$local_branch"; then
                    git checkout -b "$local_branch" --track "$remote_branch"
                    git checkout "$CURRENT_BRANCH"
                fi
                ;;
            *)
                continue
                ;;
        esac
    done < <(git branch -r | sed 's/^ *//')
    
    # Check if there are any branches in the repository
    branch_count=$(git branch --list | wc -l)
    if [ "$branch_count" -gt 0 ]; then
        # Iterate over each branch and pull changes
        while IFS= read -r branch; do
            # Skip the specified branch
            if [ "$branch" == "dev/imp/websocket_refactoring_and_pylint_audit" ]; then
                echo -e "${YELLOW}Skipping branch: $branch${NC}"
                continue
            fi

            # Check if the branch exists on the remote
            if ! git ls-remote --exit-code origin "$branch" > /dev/null 2>&1; then
                echo "Branch '$branch' no longer exists on remote. Deleting local branch..."
                # Switch to a different branch before deleting
                active_branch=$(git rev-parse --abbrev-ref HEAD)
                if [ "$active_branch" == "$branch" ]; then
                    git checkout "$ORIGINAL_BRANCH" > /dev/null 2>&1 || continue
                fi
                # Delete the local branch
                git branch -D "$branch"
                ((DELETED_BRANCHES++))
                echo -e "${YELLOW}Branch '$branch' deleted locally${NC}"
                DELETED_BRANCHES_LIST+=("$branch")
                continue
            fi

            # Pull target deploy branches, plus other branches whose open PR is
            # assigned to one of the configured GitHub users.
            if ! should_pull_branch "$branch"; then
                if branch_assigned_to_user "$branch"; then
                    echo -e "${BLUE}Pulling assigned branch: $branch (assignee: $BRANCH_PULL_ASSIGNEES)${NC}"
                else
                    continue
                fi
            fi

            echo "-----------------"
            echo "Pulling from branch $branch"
            git checkout "$branch"

            # Pull changes from the branch
            if pull_output=$(git pull --recurse-submodules); then
                if [[ $pull_output == *"Already up to date."* ]]; then
                    echo -e "${BLUE}At the Latest Commit${NC}"
                    ((NO_CHANGES++))
                    NO_CHANGES_BRANCHES+=("$branch")
                else
                    echo -e "${GREEN}UPDATE: SUCCESSFUL${NC}"
                    ((SUCCESSFUL_PULLS++))
                    SUCCESSFUL_BRANCHES+=("$branch")
                fi
            else
                echo -e "${RED}UPDATE: FAILED${NC}"
                ((FAILED_PULLS++))
                FAILED_BRANCHES+=("$branch")
            fi
        done < <(git branch --list | cut -c 3-)
    else
        echo "No branches found in $repo_dir"
    fi

    # Navigate back to the original branch
    git checkout "$ORIGINAL_BRANCH" > /dev/null 2>&1 || continue

done < <(find . -type d -name ".git" -print0)

cd "$REPO_ROOT" || exit 1
git pull --recurse-submodules

# Print summary report
echo "-----------------"
echo -e "Summary:"
echo -e "${BLUE}At the Latest Commit: $NO_CHANGES${NC}"
echo -e "${GREEN}Successful Pulls: $SUCCESSFUL_PULLS${NC}"
echo -e "${RED}Failed Pulls: $FAILED_PULLS${NC}"
echo -e "${YELLOW}Deleted Branches: $DELETED_BRANCHES${NC}"
echo "-----------------"
# Print list of branches with successful pulls
if [ ${#SUCCESSFUL_BRANCHES[@]} -gt 0 ]; then
    echo -e "${GREEN}Branches with New Commits:${NC}"
    for branch in "${SUCCESSFUL_BRANCHES[@]}"; do
        echo "$branch"
    done
    echo "-----------------"
fi
# Print list of branches with failed pulls
if [ ${#FAILED_BRANCHES[@]} -gt 0 ]; then
    echo -e "${RED}Branches with Failed Pulls:${NC}"
    for branch in "${FAILED_BRANCHES[@]}"; do
        echo "$branch"
    done
    echo "-----------------"
fi

# Print list of deleted branches
if [ ${#DELETED_BRANCHES_LIST[@]} -gt 0 ]; then
    echo -e "${YELLOW}Deleted Branches:${NC}"
    for branch in "${DELETED_BRANCHES_LIST[@]}"; do
        echo "$branch"
    done
    echo "-----------------"
fi
echo "-----------------"
# Print current branch
echo "You are on Branch:"
echo -e "${PURPLE}$ORIGINAL_BRANCH${NC}"
echo "-----------------"
echo "-----------------"
# Run branch_management.py
if [ "$REPO_ROOT" == "/Users/niman/Desktop/Pad/Work/Trajekt/ArcMachine" ]; then
    echo -e "${PURPLE}Running branch_management.py...${NC}"
    python3 /Users/niman/Devs_and_ML/Code_Maintenance/branch_management.py
    echo "-----------------"
    echo "-----------------"
fi
# Cleanup and stash changes
rm -rf "$REPO_ROOT/core_utils"
git stash
