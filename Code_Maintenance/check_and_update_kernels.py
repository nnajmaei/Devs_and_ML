import os
import sys
import nbformat

# Ensure the directory is passed as an argument
if len(sys.argv) < 2:
    print("Error: Please provide the project directory as an argument.")
    sys.exit(1)

# Use the directory passed as an argument
project_directory = sys.argv[1]

# Define the desired kernel name
desired_kernel = "arc"


# Function to update the kernel in an IPython notebook
def update_kernel(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        notebook = nbformat.read(f, as_version=4)

    # Ensure kernelspec exists in metadata, if not, create it
    kernelspec = notebook["metadata"].get("kernelspec", {})

    # Get the original kernel (if it exists)
    original_kernel = kernelspec.get("name", "No kernel specified")

    # Prepare the relative file path
    relative_file_path = os.path.relpath(file_path, project_directory)

    # Define column widths
    file_column_width = 100
    original_kernel_column_width = 25

    # Check if the kernel is already 'arc'
    if original_kernel == desired_kernel:
        # Print message if no change is needed
        # print(
        #     f"File {relative_file_path.ljust(file_column_width)}: no change needed (already {desired_kernel.ljust(original_kernel_column_width)})"
        # )
        return

    # Update the kernel
    notebook["metadata"]["kernelspec"] = {
        "name": desired_kernel,
        "display_name": desired_kernel,
    }

    # Write the updated notebook back to file
    with open(file_path, "w", encoding="utf-8") as f:
        nbformat.write(notebook, f)

    # Print the change from original to new kernel
    print(
        f"File {relative_file_path.ljust(file_column_width)}: changed from {original_kernel.ljust(original_kernel_column_width)} to {desired_kernel}"
    )


# Walk through the project directory and find all .ipynb files, excluding 'archive/'
for root, dirs, files in os.walk(project_directory):
    # Exclude the 'archive/' folder
    dirs[:] = [d for d in dirs if d != "archive"]

    for file in files:
        if file.endswith(".ipynb"):
            file_path = os.path.join(root, file)
            update_kernel(file_path)

print("Kernel update complete!")
