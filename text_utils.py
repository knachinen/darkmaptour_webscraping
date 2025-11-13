import json
import os
from typing import Any, Dict, List, Union
from datetime import datetime

def get_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def save_json_data(data: Union[Dict, List], filepath: str) -> bool:
    """
    Saves a Python dictionary or list to a specified JSON file.

    Args:
        data: The Python object (dict or list) to be saved.
        filepath: The full path to the output JSON file.

    Returns:
        True if the save was successful, False otherwise.
    """
    try:
        # Open the file for writing ('w')
        with open(filepath, 'w', encoding='utf-8') as f:
            # Use json.dump() to write the data to the file
            # added indent for readability and ensure_ascii=False for handling non-ASCII characters
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved data to '{filepath}'")
        return True
    except TypeError as e:
        print(f"ERROR saving data: Object is not JSON serializable. Details: {e}")
        return False
    except IOError as e:
        print(f"ERROR saving data: Could not write to file '{filepath}'. Details: {e}")
        return False


def load_json_data(filepath: str) -> Union[Dict, List, None]:
    """
    Loads data from a specified JSON file and returns it as a Python dictionary or list.

    Args:
        filepath: The full path to the input JSON file.

    Returns:
        The loaded Python object (dict or list) on success, or None on failure.
    """
    # 1. Check if the file exists first
    if not os.path.exists(filepath):
        print(f"File not found: '{filepath}'. Returning None.")
        return None

    try:
        # Open the file for reading ('r')
        with open(filepath, 'r', encoding='utf-8') as f:
            # Use json.load() to parse the JSON data from the file object
            data = json.load(f)
        print(f"Successfully loaded data from '{filepath}'")
        return data

    except json.JSONDecodeError as e:
        print(f"ERROR loading data: Failed to decode JSON in '{filepath}'. Details: {e}")
        return None
    except IOError as e:
        print(f"ERROR loading data: Could not read from file '{filepath}'. Details: {e}")
        return None


def clean_text(text: str) -> str:
    flag = True
    while flag:
        flag_space = True if '  ' in text else False
        flag_linefeed = True if '\n\n' in text else False
        if flag_space or flag_linefeed:
            if flag_space:
                text = text.replace('  ', ' ')
            if flag_linefeed:
                text = text.replace('\n\n', '\n')
        else:
            flag = False
    return text.strip()
