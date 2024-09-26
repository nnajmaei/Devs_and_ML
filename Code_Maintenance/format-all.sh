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

# Ask the user if the default directory is correct
echo "The default directory is: ${GRAY}$DEFAULT_DIR${NC}"
read -p "Is this the directory you want to use? (y/n): " user_response

if [ "$user_response" != "y" ]; then
    # Ask for the new directory path
    read -p "Please enter the path to the new directory: " new_directory
    if [ -d "$new_directory" ]; then
        cd "$new_directory" || exit
    else
        echo -e "${RED}Directory does not exist. Exiting.${NC}"
        exit 1
    fi
else
    # Navigate to the default directory
    cd "$DEFAULT_DIR" || exit
fi

# Ask the user if they want to perform all tasks or specific ones
echo "Do you want to perform all tasks?"
read -p "Enter 'y' to perform all tasks or 'n' to choose specific tasks: " all_tasks

tasks_to_run=(1 2 3 4 5)

if [ "$all_tasks" != "y" ]; then
    echo "Available tasks:"
    echo "1- Removing unused imports using Autoflake"
    echo "2- Formatting code using Black"
    echo "3- Formatting JSONs using Prettier"
    echo "4- Clearing Jupyter notebook outputs"
    echo "5- Reporting missing imports in the project"
    read -p "Enter the numbers associated with the tasks you want to perform (e.g., 1, 4, 3): " selected_tasks
    IFS=', ' read -r -a tasks_to_run <<< "$selected_tasks"
fi

git add .
echo "--------------------------------------------------------------------------------"
echo -e "${BLUE}Starting format-all.sh script...${NC}"
echo "--------------------------------------------------------------------------------"

# Check if task 1 is selected
if [[ " ${tasks_to_run[*]} " =~ " 1 " ]]; then
    echo -e "${DARK_BLUE}1- Removing unused imports using Autoflake...${NC}"
    autoflake --remove-all-unused-imports --ignore-pass-after-docstring --recursive --in-place ./ArcPyUtils ./notebooks  ./notebooks-updated  ./daemons
    echo " "
    # Save the count of changed files in a variable
    autoflake_changed_files_count=$(git diff --name-only | wc -l)

    # Use an if statement to check if the count is non-zero
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
    # Black: format code
    echo -e "${DARK_BLUE}2- Formatting code using Black...${NC}"
    black ./
    echo " "

    # Save the count of changed files in a variable
    changed_files_count=$(git diff --name-only | wc -l)

    # Use an if statement to check if the count is non-zero
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
    # Prettier: format code
    echo -e "${DARK_BLUE}3- Formatting JSONs using Prettier...${NC}"
    npx prettier --write ./
    echo " "
    # Save the count of changed files in a variable
    changed_files_count=$(git diff --name-only | wc -l)

    # Use an if statement to check if the count is non-zero
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
    # Clear Jupyter notebook outputs
    echo -e "${DARK_BLUE}4- Clearing Jupyter notebook outputs...${NC}"
    python - << EOF
import os
import nbformat

def clear_outputs_and_execution_count(notebook_path):
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    for cell in nb.cells:
        if cell.cell_type == "code":
            cell["outputs"] = []
            cell["execution_count"] = None

    with open(notebook_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)

def process_folder(folder_path):
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".ipynb"):
                notebook_path = os.path.join(root, file)
                clear_outputs_and_execution_count(notebook_path)

folders = ["./notebooks", "./notebooks-updated"]
for folder in folders:
    if os.path.exists(folder):
        process_folder(folder)
    else:
        print(f"Folder {folder} does not exist.")
EOF
    echo " "
    # Save the count of changed files in a variable
    changed_files_count=$(git diff --name-only | wc -l)

    # Use an if statement to check if the count is non-zero
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

# Check if task 5 is selected
if [[ " ${tasks_to_run[*]} " =~ " 5 " ]]; then
    # Check for missing imports in the project (inlined check_imports_in_project.py)
    echo -e "${DARK_BLUE}5- Reporting missing imports in the project...${NC}"
    files_with_issues_count=$(python - << EOF
import os
import ast
import importlib.util

EXCLUDED_DIRS = [
    "/arc",
    "/notebooks-updated",
    "/notebooks",
    "/arc_testing",
    "/archive",
    "/core_utils",
]

EXCLUDED_FILES = [
    "TrajektBallDetection/trajektballdetection/circle_detection/new_hough_circle_detector.py",
    "daemons/alpha_controller/tests/test_mock_alpha.py",
    "daemons/pos_controller/MachineMotion_v4_6.py",
    "daemons/wheel_speed_controller/controllers/gmc.py",
]
IGNORED_MODULES = []
IGNORED_PREFIXES = []

def find_imports_in_file(file_path):
    imports = []
    with open(file_path, "r", encoding="utf-8") as file:
        try:
            tree = ast.parse(file.read(), filename=file_path)
        except SyntaxError:
            return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return imports

def check_module_exists(module_name):
    if module_name in IGNORED_MODULES:
        return True

    if any(module_name.startswith(prefix) for prefix in IGNORED_PREFIXES):
        return True

    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return False
        return True
    except (ModuleNotFoundError, ValueError, ImportError):
        return False

def check_project_imports(project_dir):
    missing_imports = []
    unique_files_with_issues = set()

    for root, dirs, files in os.walk(project_dir):
        if any(exclude_dir in root for exclude_dir in EXCLUDED_DIRS):
            continue

        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                relative_file_path = os.path.relpath(file_path, start=project_dir)
                if relative_file_path in EXCLUDED_FILES:
                    continue

                imports = find_imports_in_file(file_path)

                for module in imports:
                    if not check_module_exists(module):
                        missing_imports.append((file_path, module))
                        unique_files_with_issues.add(file_path)

    return missing_imports, len(unique_files_with_issues)

if __name__ == "__main__":
    project_directory = os.path.dirname(os.path.abspath(__file__))
    missing_imports, files_with_issues_count = check_project_imports(project_directory)

    if missing_imports:
        max_file_path_length = max(
            len(os.path.relpath(file_path, start=project_directory))
            for file_path, _ in missing_imports
        )

        current_file = None
        for idx, (file_path, module) in enumerate(missing_imports):
            relative_path = os.path.relpath(file_path, start=project_directory)

            if file_path != current_file:
                if current_file is not None:
                    print("-" * (max_file_path_length + 30))

                print(
                    f"File: {relative_path:<{max_file_path_length}}   Missing Module: {module}"
                )
                current_file = file_path
            else:
                print(f"{'':<{max_file_path_length + 6}}   Missing Module: {module}")

        # Color-coded output based on the number of files with issues
        if files_with_issues_count > 0:
            print(f"\n${RED}Number of files with import issues: {files_with_issues_count}${NC}")
    else:
        print(f"\n${GREEN}All imports seem valid${NC}")
    
    # Print the file_with_issues_count to be captured by the bash script
    print(files_with_issues_count)
EOF
    )


    # Assuming `files_with_issues_count` contains the whole output

    before_last_entry=$(echo "$files_with_issues_count" | awk 'NR==1,/Number of files with import issues:/')
    last_entry=$(echo "$files_with_issues_count" | awk '/Number of files with import issues:/,EOF' | tail -n 1)

    # Optionally trim whitespace if necessary
    before_last_entry=$(echo "$before_last_entry" | sed 's/[[:space:]]*$//')
    last_entry=$(echo "$last_entry" | sed 's/^[[:space:]]*//')

    echo "$before_last_entry"


    echo "--------------------------------------------------------------------------------"
fi

git reset
echo -e "${BLUE}=== SUMMARY ===${NC}"

# Save the count of changed files in a variable
changed_files_count=$(git diff --name-only | wc -l)

# Use an if statement to check if the count is non-zero
if [ "$changed_files_count" -ne 0 ]; then
    echo -e "${RED}Number of changed files: $changed_files_count${NC}"
    echo -e "${GRAY}Files Changed :${NC}"
    git status
    echo " "
else
    echo -e "${GREEN}No Files Changed${NC}"

fi

# Convert last_entry to an integer
last_entry_int=$(echo "$last_entry" | tr -d '[:space:]')  # Remove any surrounding whitespace

# Check if last_entry is non-zero
if (( last_entry_int != 0 )); then
    echo -e "${RED}Files With Import Issues: $last_entry_int${NC}"
else
    echo -e "${GREEN}No Files with Import Issues${NC}"
fi
