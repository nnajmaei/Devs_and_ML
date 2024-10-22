#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
DARK_BLUE='\033[1;34m'
GRAY='\033[2;37m'  # Dim white
NC='\033[0m' # No Color

# Default directory
DEFAULT_DIR="/Users/niman/Desktop/Pad/Work/Trajekt/ArcMachine/"
echo "--------------------------------------------------------------------------------"
echo -e "${BLUE}Starting format-all.sh script...${NC}"
echo " "

# Ask the user if the default directory is correct
echo -e "The default directory is: ${BLUE}$DEFAULT_DIR${NC}"
read -p "Is this the directory you want to use? (y/n): " user_response

if [ "$user_response" != "y" ]; then
    # Ask for the new directory path
    read -p "Please enter the path to the new directory: " new_directory
    if [ -d "$new_directory" ]; then
        project_directory="$new_directory"
        cd "$new_directory" || exit
    else
        echo -e "${RED}Directory does not exist. Exiting.${NC}"
        exit 1
    fi
else
    # Navigate to the default directory
    project_directory="$DEFAULT_DIR"
    cd "$DEFAULT_DIR" || exit
fi

# Function to check if input is a valid list of numbers
is_valid_task_numbers() {
    echo "$1" | grep -Eq '^([0-9]+[ ,]*)+$'
}

# Function to normalize input (removes spaces and commas)
normalize_task_input() {
    # Replace any commas or spaces with a single comma, then trim commas
    echo "$1" | sed 's/[ ,]\+/,/g' | sed 's/^,\|,$//g'
}

# Validate user input: 'y', 'n', or comma/space-separated numbers
while true; do
    echo " "
    echo "Do you want to perform all tasks, select specific tasks, or provide task numbers directly?"
    read -p "Enter 'y' to perform all tasks, 'n' to choose specific tasks, or task numbers (e.g., 1 4 3 or 1,4,3): " user_input

    if [[ "$user_input" == "y" || "$user_input" == "n" ]]; then
        break
    elif is_valid_task_numbers "$user_input"; then
        user_input=$(normalize_task_input "$user_input")
        break
    else
        echo -e "${RED}Invalid input. Please enter 'y', 'n', or a comma/space-separated list of task numbers.${NC}"
    fi
done

tasks_to_run=(1 2 3 4 5 6)

if [[ "$user_input" == "y" ]]; then
    # Perform all tasks
    echo " "
    echo "Performing all tasks..."
elif [[ "$user_input" == "n" ]]; then
    # Show the list of tasks and prompt for selection
    echo "Available tasks:"
    echo "1- Removing unused imports using Autoflake"
    echo "2- Formatting code using Black"
    echo "3- Formatting JSONs using Prettier"
    echo "4- Clearing Jupyter notebook outputs"
    echo "5- Updating Jupyter notebook kernels"
    echo "6- Reporting missing imports in the project"
    read -p "Enter the numbers associated with the tasks you want to perform (e.g., 1 4 3 or 1,4,3): " selected_tasks
    if is_valid_task_numbers "$selected_tasks"; then
        selected_tasks=$(normalize_task_input "$selected_tasks")
        IFS=',' read -r -a tasks_to_run <<< "$selected_tasks"
    else
        echo -e "${RED}Invalid task numbers. Exiting.${NC}"
        exit 1
    fi
else
    # Assume user entered task numbers directly
    IFS=',' read -r -a tasks_to_run <<< "$user_input"
    echo " "
    echo "Performing selected tasks: ${tasks_to_run[*]}"
fi

echo " "
git add .
echo "--------------------------------------------------------------------------------"

# Check if task 1 is selected
if [[ " ${tasks_to_run[*]} " =~ " 1 " ]]; then
    echo -e "${DARK_BLUE}1- Removing unused imports using Autoflake...${NC}"
    echo -e "${GRAY}Inclusions: ArcPyUtils, notebooks, notebooks-updated, daemons${NC}"
    autoflake --remove-all-unused-imports --ignore-pass-after-docstring --recursive --in-place ./ArcPyUtils ./notebooks  ./notebooks-updated  ./daemons
    echo " "
    autoflake_changed_files_count=$(git diff --name-only | wc -l)

    if [ "$autoflake_changed_files_count" -ne 0 ]; then
        echo -e "${RED}Number of changed files: $autoflake_changed_files_count${NC}"
        echo -e "${GRAY}Files Changed so far:${NC}"
        git diff --name-only
        git add .
    else
        echo -e "${GREEN}No Files Changed${NC}"
    fi
    echo "--------------------------------------------------------------------------------"
fi

# Check if task 2 is selected
if [[ " ${tasks_to_run[*]} " =~ " 2 " ]]; then
    echo -e "${DARK_BLUE}2- Formatting code using Black...${NC}"
    echo -e "${GRAY}Exclusions: None${NC}"
    black ./
    echo " "
    changed_files_count=$(git diff --name-only | wc -l)

    if [ "$changed_files_count" -ne 0 ]; then
        echo -e "${RED}Number of changed files: $changed_files_count${NC}"
        echo -e "${GRAY}Files Changed :${NC}"
        git diff --name-only
        git add .
    else
        echo -e "${GREEN}No Files Changed${NC}"
    fi
    echo "--------------------------------------------------------------------------------"
fi

# Check if task 3 is selected
if [[ " ${tasks_to_run[*]} " =~ " 3 " ]]; then
    echo -e "${DARK_BLUE}3- Formatting JSONs using Prettier...${NC}"
    echo -e "${GRAY}Inclusions: All JSON files${NC}"
    npx prettier --write ./
    echo " "
    changed_files_count=$(git diff --name-only | wc -l)

    if [ "$changed_files_count" -ne 0 ]; then
        echo -e "${RED}Number of changed files: $changed_files_count${NC}"
        echo -e "${GRAY}Files Changed :${NC}"
        git diff --name-only
        git add .
    else
        echo -e "${GREEN}No Files Changed${NC}"
    fi
    echo "--------------------------------------------------------------------------------"
fi

# Check if task 4 is selected
if [[ " ${tasks_to_run[*]} " =~ " 4 " ]]; then
    echo -e "${DARK_BLUE}4- Clearing Jupyter notebook outputs...${NC}"
    echo -e "${GRAY}Inclusions: All Jupyter notebooks in notebooks, notebooks-updated${NC}"
    python /Users/niman/Devs_and_ML/Code_Maintenance/clear_notebook_outputs.py
    echo " "
    changed_files_count=$(git diff --name-only | wc -l)

    if [ "$changed_files_count" -ne 0 ]; then
        echo -e "${RED}Number of changed files: $changed_files_count${NC}"
        echo -e "${GRAY}Files Changed :${NC}"
        git diff --name-only
        git add .
    else
        echo -e "${GREEN}No Files Changed${NC}"
    fi
    echo "--------------------------------------------------------------------------------"
fi

# Check if task 5 is selected (now updating Jupyter notebook kernels)
if [[ " ${tasks_to_run[*]} " =~ " 5 " ]]; then
    echo -e "${DARK_BLUE}5- Updating Jupyter notebook kernels...${NC}"

    # Call the external Python script to update kernels
    python3 /Users/niman/Devs_and_ML/Code_Maintenance/check_and_update_kernels.py "$project_directory"

    echo " "
    changed_files_count=$(git diff --name-only | wc -l)

    if [ "$changed_files_count" -ne 0 ]; then
        echo -e "${RED}Number of changed files: $changed_files_count${NC}"
        echo -e "${GRAY}Files Changed :${NC}"
        git diff --name-only
        git add .
    else
        echo -e "${GREEN}No Files Changed${NC}"
    fi
    echo "--------------------------------------------------------------------------------"
fi

# Check if task 6 is selected (now reporting missing imports)
if [[ " ${tasks_to_run[*]} " =~ " 6 " ]]; then
    echo -e "${DARK_BLUE}6- Reporting missing imports in the project...${NC}"
    echo -e "${GRAY}Exclusions: EXCLUDED_DIRS (/arc, /arc_testing, /archive, /core_utils)${NC}"
    echo -e "${GRAY}Exclusions: EXCLUDED_FILES (TrajektBallDetection/trajektballdetection/circle_detection/new_hough_circle_detector.py, daemons/alpha_controller/tests/test_mock_alpha.py, daemons/pos_controller/MachineMotion_v4_6.py, daemons/wheel_speed_controller/controllers/gmc.py)${NC}"
    files_with_issues_count=$(python /Users/niman/Devs_and_ML/Code_Maintenance/check_missing_imports.py "$project_directory")

    last_entry=$(echo "$files_with_issues_count" | tail -n 1)
    before_last_entry=$(echo "$files_with_issues_count" | sed '$d')
    before_last_entry=$(echo "$before_last_entry" | sed 's/[[:space:]]*$//')
    last_entry=$(echo "$last_entry" | sed 's/^[[:space:]]*//')
    last_entry_int=$(echo "$last_entry" | tr -d '[:space:]')

    if (( last_entry_int != 0 )); then
        echo -e "${RED}${before_last_entry}${NC}"
        echo -e "${RED}Number of files with import issues: $last_entry_int${NC}"
    else
        echo -e "${GREEN}${before_last_entry}${NC}"
    fi

    echo "--------------------------------------------------------------------------------"
fi

git reset
echo -e "${BLUE}=== SUMMARY ===${NC}"

changed_files_count=$(git diff --name-only | wc -l)

if [ "$changed_files_count" -ne 0 ]; then
    echo -e "${RED}Number of changed files: $changed_files_count${NC}"
    echo -e "${GRAY}Files Changed :${NC}"
    git status
    echo " "
else
    echo -e "${GREEN}No Files Changed${NC}"
fi

if (( last_entry_int != 0 )); then
    echo -e "${RED}Files With Import Issues: $last_entry_int${NC}"
else
    echo -e "${GREEN}No Files with Import Issues${NC}"
fi
