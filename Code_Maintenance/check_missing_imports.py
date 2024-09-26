import os
import sys
import ast
import importlib.util

# Directories and files to exclude
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


# Add project directory to sys.path to search for modules within the project
def add_project_to_syspath(project_dir):
    if project_dir not in sys.path:
        sys.path.append(project_dir)


# Find all imports in a file
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
                # Handle relative imports (e.g., from .module import ...)
                imports.append(node.module)
    return imports


# Check if a module exists in the current Python environment or project directory
def check_module_exists(module_name, project_dir):
    if module_name in IGNORED_MODULES:
        return True

    if any(module_name.startswith(prefix) for prefix in IGNORED_PREFIXES):
        return True

    # Handle relative imports by checking if the module is within the project directory
    if module_name.startswith("."):
        # Resolve relative import path based on project structure
        relative_path = module_name.replace(".", "/")
        module_path = os.path.join(project_dir, relative_path)
        if os.path.exists(module_path) or os.path.exists(f"{module_path}.py"):
            return True
        return False

    try:
        # Search for the module in sys.path and installed packages
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return False
        return True
    except (ModuleNotFoundError, ValueError, ImportError):
        return False


# Check all imports in the project for missing modules
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
                    if not check_module_exists(module, project_dir):
                        missing_imports.append((file_path, module))
                        unique_files_with_issues.add(file_path)

    return missing_imports, len(unique_files_with_issues)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        project_directory = sys.argv[1]
    else:
        project_directory = os.path.dirname(os.path.abspath(__file__))

    # Add project directory to sys.path so local imports can be found
    add_project_to_syspath(project_directory)

    # Check for missing imports
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

        if files_with_issues_count > 0:
            print(f"\nNumber of files with import issues: {files_with_issues_count}")
    else:
        print("\nAll imports seem valid")

    print(files_with_issues_count)
