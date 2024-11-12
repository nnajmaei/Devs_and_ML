import json
import sys
from pathlib import Path

# Adding the path for importing specific classes
sys.path.insert(
    0, "/Users/niman/Desktop/Pad/Work/Trajekt/ArcMachine/ArcPyUtils/arcpyutils/enums"
)

# Import required classes
from errorID import (  # type: ignore
    ProcessErrorPrefix,
    AxisErrorPrefix,
    SensorErrorPrefix,
    MiscErrorPrefix,
    ErrorIDMixin,
    ErrorID,
)


def extract_error_ids(file_path):
    """Extracts error IDs from a JSON file and identifies those with whitespace."""
    try:
        with open(file_path, "r") as file:
            data = json.load(file)

            # Extract all error IDs from JSON
            error_ids = [item.get("errorID") for item in data if "errorID" in item]

            # Identify error IDs with whitespace
            ids_with_whitespace = [
                error_id
                for error_id in error_ids
                if error_id and (" " in error_id or error_id != error_id.strip())
            ]

            return error_ids, ids_with_whitespace
    except Exception as e:
        print(f"An error occurred: {e}")
        return [], []


def get_error_values():
    """Gets error values from specific ErrorID classes."""
    error_values = []
    for error_class in [ErrorID.Axis, ErrorID.Misc, ErrorID.Process, ErrorID.Sensor]:
        for error in error_class:
            error_values.append(error.value)
    return error_values


def find_unique_and_partial_matches(list1, list2, name1="list1", name2="list2"):
    """Finds unique items between two lists and separates partial matches."""
    unique_dict = {}
    partial_matches = {}

    # Check each item in list1
    for item in list1:
        if item not in list2:
            # Check for partial matches in list2
            partial_match = next(
                (
                    other_item
                    for other_item in list2
                    if item in other_item or other_item in item
                ),
                None,
            )
            if partial_match:
                partial_matches[item] = (name1, name2, partial_match)
            else:
                unique_dict[item] = (name1, name2)

    # Check each item in list2
    for item in list2:
        if item not in list1:
            # Check for partial matches in list1
            partial_match = next(
                (
                    other_item
                    for other_item in list1
                    if item in other_item or other_item in item
                ),
                None,
            )
            if partial_match:
                partial_matches[item] = (name2, name1, partial_match)
            else:
                unique_dict[item] = (name2, name1)

    return unique_dict, partial_matches


# Paths
file_path = (
    "/Users/niman/Desktop/Pad/Work/Trajekt/ArcMachine/errorIDs_list/ErrorIDs.json"
)

# Run the functions
error_ids, ids_with_whitespace = extract_error_ids(file_path)
error_values_list = get_error_values()

# Find unique and partial matches between error_ids (from JSON) and error_values_list (from ErrorID classes)
unique_dict, partial_matches = find_unique_and_partial_matches(
    error_ids, error_values_list, "csv_list", "error_list"
)

# Print unique items
if unique_dict:
    max_error_id_length = max(len(error_id) for error_id in unique_dict.keys())
    print(
        f"\n{'Error ID':<{max_error_id_length}} {'Present in':<15} {'Missing in':<15}"
    )
    print("-" * (max_error_id_length + 30))
    for error_id, (present_list, missing_list) in unique_dict.items():
        print(
            f"{error_id:<{max_error_id_length}} {present_list:<15} {missing_list:<15}"
        )
else:
    print("No unique items found. Both lists contain the same items.")

# Print partial matches
if partial_matches:
    max_error_id_length = max(len(error_id) for error_id in partial_matches.keys())
    print(
        f"\n{'Error ID':<{max_error_id_length}} {'Present in':<15} {'Partial match in':<15} {'Partial match':<20}"
    )
    print("-" * (max_error_id_length + 50))
    for error_id, (
        present_list,
        partial_list,
        partial_match,
    ) in partial_matches.items():
        print(
            f"{error_id:<{max_error_id_length}} {present_list:<15} {partial_list:<15} {partial_match:<20}"
        )
else:
    print("No partial matches found.")
