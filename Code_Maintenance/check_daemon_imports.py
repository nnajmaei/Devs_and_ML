import os
import re


def find_daemon_imports(directory):
    # Regex to match import statements for "daemons"
    daemon_import_pattern = re.compile(r"^\s*(from|import)\s+daemons")

    # List to store files with "daemons" imports
    files_with_daemon_imports = []

    # Walk through the directory and check each Python file
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    # Check each line for "daemons" import
                    if any(daemon_import_pattern.search(line) for line in f):
                        files_with_daemon_imports.append(file_path)
                        break

    # Print results
    if files_with_daemon_imports:
        print("Files with 'daemons' imports:")
        for file in files_with_daemon_imports:
            print(file)
    else:
        print("No 'daemons' imports found in any Python files.")


# Directory to search
directory_to_search = "/Users/niman/Desktop/Pad/Work/Trajekt/ArcMachine/ArcPyUtils"

# Run the function
find_daemon_imports(directory_to_search)
