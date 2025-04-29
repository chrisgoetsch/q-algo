# File: utils/atomic_write.py

import os
import tempfile
import json

def atomic_write_json(filepath, data):
    """
    Safely write JSON data atomically.
    """
    dir_name = os.path.dirname(filepath)
    with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False) as tmp_file:
        json.dump(data, tmp_file, indent=2)
        temp_path = tmp_file.name

    os.replace(temp_path, filepath)

def atomic_append_jsonl(filepath, entry):
    """
    Safely append a JSONL entry atomically.
    """
    dir_name = os.path.dirname(filepath)
    with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False) as tmp_file:
        if os.path.exists(filepath):
            with open(filepath, 'r') as original_file:
                tmp_file.writelines(original_file.readlines())
        tmp_file.write(json.dumps(entry) + "\n")
        temp_path = tmp_file.name

    os.replace(temp_path, filepath)
