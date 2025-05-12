import json
import os
import shutil
from datetime import datetime

DATA_DIR = "data"
HANDLES_FILE = os.path.join(DATA_DIR, "handles.json")
SOLVED_PROBLEMS_FILE = os.path.join(DATA_DIR, "solved_problems.json")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")


def ensure_data_dir_exists():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)

def load_handles():
    ensure_data_dir_exists()
    if not os.path.exists(HANDLES_FILE):
        return []
    try:
        with open(HANDLES_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return [] # Return empty list if file is corrupted or empty

def save_handles(handles):
    ensure_data_dir_exists()
    with open(HANDLES_FILE, 'w') as f:
        json.dump(sorted(list(set(handles))), f, indent=4)

def add_handle(handle):
    handles = load_handles()
    if handle not in handles:
        handles.append(handle)
        save_handles(handles)
        return True
    return False

def remove_handle(handle):
    handles = load_handles()
    if handle in handles:
        handles.remove(handle)
        save_handles(handles)
        return True
    return False

def load_solved_problems_data():
    ensure_data_dir_exists()
    if not os.path.exists(SOLVED_PROBLEMS_FILE):
        return []
    try:
        with open(SOLVED_PROBLEMS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return [] # Return empty list if file is corrupted or empty

def save_solved_problems_data(problems_data):
    ensure_data_dir_exists()
    # Backup before saving
    if os.path.exists(SOLVED_PROBLEMS_FILE):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKUP_DIR, f"solved_problems_{timestamp}.json")
        try:
            shutil.copy2(SOLVED_PROBLEMS_FILE, backup_file)
        except Exception as e:
            print(f"Warning: Could not create backup: {e}")

    with open(SOLVED_PROBLEMS_FILE, 'w') as f:
        json.dump(problems_data, f, indent=4)

