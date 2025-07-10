import os
import json
from pathlib import Path


def append_json_to_file(data, path, verbose: bool = True):
    '''
        Save data to a file, will be appended if file already exists.
        The file will be saved in the logs/tokens_used directory.
        The file will be named tokens_used_<session_id>.json
    '''
    
    if verbose:
        print(f"Append to file {path}...")
    
    # Load existing data if the file exists
    if os.path.exists(path):
        with open(path, 'r') as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    # Append new tokens used to existing data
    existing_data.append(data)

    with open(path, 'w') as f:
        json.dump(existing_data, f, indent=4)
    
    if verbose:
        print("File written:", os.path.exists(path), "Size:", os.path.getsize(path))


def save_json_to_file(data, path: Path, verbose: bool = True):

    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

    if verbose:
        print("File written:", os.path.exists(path), "Size:", os.path.getsize(path))

def load_json(path):
    """
    Load a JSON file from the given path and return its contents as a Python object.
    """
    # check if file exists
    if not path.exists():
        raise FileNotFoundError(f"Path {path} does not exist.")

    # check if file is json
    if not path.suffix == '.json':
        raise ValueError(f"Path {path} is not a JSON file.")

    with open(path, 'r', encoding="utf8") as f:
        return json.load(f)
