#!/bin/bash

# ANSI color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Store the current branch
ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)

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

# Navigate to the specified directory
cd "/Users/niman/Desktop/Pad/Work/Trajekt/ArcMachine/" || exit

# Fetch the latest changes and prune remote branches in the repository directory
git fetch --all --prune
git remote prune origin

# Trap for any errors or when script exits prematurely
trap 'git checkout "$ORIGINAL_BRANCH"' EXIT

# Find all git repositories recursively
while IFS= read -r -d '' git_dir; do
    # Navigate to the parent directory of the .git directory
    repo_dir="$(dirname "$git_dir")"
    # Navigate into the repository directory
    cd "$repo_dir" || continue
    
    # Store the current branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    
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
            
            echo "-----------------"
            echo "Pulling from branch $branch"
            git checkout "$branch"
            
            # Check if the branch exists on the remote
            if ! git ls-remote --exit-code origin "$branch" > /dev/null 2>&1; then
                echo "Branch '$branch' no longer exists on remote. Deleting local branch..."
                # Switch to a different branch before deleting
                git checkout "$ORIGINAL_BRANCH"
                # Delete the local branch
                git branch -D "$branch"
                ((DELETED_BRANCHES++))
                echo -e "${YELLOW}Branch '$branch' deleted locally${NC}"
                DELETED_BRANCHES_LIST+=("$branch")
                continue
            fi
            
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
