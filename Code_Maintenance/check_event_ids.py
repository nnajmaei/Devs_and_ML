import os
import re

# Define the directory to search in (current working directory)
project_directory = "/Users/niman/Desktop/Pad/Work/Trajekt/ArcMachine"
output_file = "eventid_lines.txt"
excluded_folders = {"arc/"}


def extract_eventid_lines(directory):
    eventid_lines = []
    eventid_pattern = re.compile(
        r"\bEventID\.", re.IGNORECASE
    )  # Case-insensitive search
    exclude_pattern = re.compile(r"\.value")  # Exclude lines containing .value
    exclude_pattern2 = re.compile(
        r'EventID.Process.NOT_IMPLEMENTED.value  # "process-not-implemented"'
    )  # Exclude lines containing error_id_module.

    # Walk through all files in the directory and subdirectories
    for root, _, files in os.walk(directory):
        # Skip excluded folders
        if any(excluded_folder in root for excluded_folder in excluded_folders):
            continue

        for file in files:
            if file.endswith(".py"):  # Only process Python files
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        multi_line_buffer = ""
                        for line_number, line in enumerate(f, start=1):
                            full_line = multi_line_buffer + line.strip()
                            if (
                                eventid_pattern.search(full_line)
                                and exclude_pattern.search(full_line)
                                and not exclude_pattern2.search(full_line)
                            ):
                                eventid_lines.append(
                                    f"{file_path} (Line {line_number}): {full_line}\n"
                                )

                            # Handle multi-line statements
                            if line.strip().endswith("\\"):
                                multi_line_buffer += line.strip()
                            else:
                                multi_line_buffer = ""
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    # Save results to a text file

    event_count = len(eventid_lines)
    color = "\033[91m" if event_count > 0 else "\033[92m"  # Red if > 0, Green otherwise
    reset = "\033[0m"

    print(f"{color}Extraction complete. Found {event_count} lines.{reset}")

    for line in eventid_lines:
        print(line)


if __name__ == "__main__":
    # Run the extraction function
    extract_eventid_lines(project_directory)
