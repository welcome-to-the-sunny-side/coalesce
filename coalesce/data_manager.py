"""
Data management functionality for coalesce.
Handles all interactions with the central JSON file.
"""

import json
import os
import requests
import shutil
import time
from datetime import datetime
from pathlib import Path


class DataManager:
    """Manages all data operations for coalesce."""
    
    def __init__(self):
        """Initialize the data manager."""
        self.config_dir = os.path.expanduser("~/.coalesce")
        self.data_file = os.path.join(self.config_dir, "problems.json")
        self.handles_file = os.path.join(self.config_dir, "handles.json")
        self.backup_dir = os.path.join(self.config_dir, "backups")
        
        # Create config directory and files if they don't exist
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        if not os.path.exists(self.data_file):
            self._write_json(self.data_file, {})
        
        if not os.path.exists(self.handles_file):
            self._write_json(self.handles_file, {"handles": []})
    
    def _write_json(self, file_path, data):
        """Write data to a JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def _read_json(self, file_path):
        """Read data from a JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def backup_data(self):
        """Create a backup of the main data file."""
        if not os.path.exists(self.data_file):
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"problems_{timestamp}.json")
        shutil.copy2(self.data_file, backup_file)
        
        # Clean up old backups (keep last 10)
        backups = sorted(Path(self.backup_dir).glob("problems_*.json"))
        if len(backups) > 10:
            for backup in backups[:-10]:
                os.remove(backup)
    
    def get_handles(self):
        """Get list of handles."""
        handles_data = self._read_json(self.handles_file)
        return handles_data.get("handles", [])
    
    def add_handle(self, handle):
        """Add a handle to the list."""
        handles_data = self._read_json(self.handles_file)
        handles = handles_data.get("handles", [])
        
        if handle in handles:
            return False, f"Handle '{handle}' already exists"
        
        # Validate the handle exists on Codeforces
        url = f"https://codeforces.com/api/user.info?handles={handle}"
        response = requests.get(url)
        data = response.json()
        
        if data['status'] != 'OK':
            return False, f"Failed to validate handle '{handle}': {data.get('comment', 'Unknown error')}"
        
        handles.append(handle)
        handles_data["handles"] = handles
        self._write_json(self.handles_file, handles_data)
        return True, f"Added handle '{handle}'"
    
    def remove_handle(self, handle):
        """Remove a handle from the list."""
        handles_data = self._read_json(self.handles_file)
        handles = handles_data.get("handles", [])
        
        if handle not in handles:
            return False, f"Handle '{handle}' does not exist"
        
        handles.remove(handle)
        handles_data["handles"] = handles
        self._write_json(self.handles_file, handles_data)
        return True, f"Removed handle '{handle}'"
    
    def get_solved_problems(self, handle):
        """Get solved problems for a specific handle."""
        url = f"https://codeforces.com/api/user.status?handle={handle}"
        response = requests.get(url)
        data = response.json()
        
        if data['status'] != 'OK':
            return False, f"Failed to fetch data for {handle}: {data.get('comment', 'Unknown error')}"
        
        solved_problems = {}
        for item in data['result']:
            if item['verdict'] == 'OK':
                problem = item['problem']
                submission_id = item['id']
                
                # Skip if contestId is missing (e.g., for gym contests)
                if 'contestId' not in problem:
                    continue
                    
                contest_id = problem['contestId']
                problem_code = problem['index']
                rating = problem.get('rating', 0)  # Default to 0 if rating not available
                tags = problem.get('tags', [])
                creation_time = item.get('creationTimeSeconds', 0)
                
                # Only include problems with rating >= 800, as per original script
                if rating >= 800:
                    problem_id = f"{contest_id}{problem_code}"
                    problem_link = f"https://codeforces.com/problemset/problem/{contest_id}/{problem_code}"
                    submission_link = f"https://codeforces.com/contest/{contest_id}/submission/{submission_id}"
                    
                    if problem_id not in solved_problems:
                        solved_problems[problem_id] = {
                            "problem_id": problem_id,
                            "problem_link": problem_link,
                            "rating": rating,
                            "tags": tags,
                            "submission_id": submission_id,
                            "submission_link": submission_link,
                            "submission_time": creation_time,
                            "contest_id": contest_id,
                            "problem_code": problem_code,
                        }
        
        return True, solved_problems
    
    def update_problems_data(self):
        """Update the central JSON file with problems from all handles."""
        handles = self.get_handles()
        
        if not handles:
            return False, "No handles found. Add handles using 'coalesce add <handle>'"
        
        # Create a backup before updating
        self.backup_data()
        
        all_problems = {}
        for handle in handles:
            success, result = self.get_solved_problems(handle)
            if success:
                all_problems.update(result)
            else:
                print(f"Warning: {result}")
        
        # Write to the central JSON file
        self._write_json(self.data_file, all_problems)
        return True, f"Updated problems data with {len(all_problems)} problems"
    
    def get_problems(self, filters=None):
        """Get problems based on filters."""
        if not os.path.exists(self.data_file):
            return []
        
        problems = self._read_json(self.data_file)
        
        if not filters:
            return list(problems.values())
        
        filtered_problems = []
        for problem in problems.values():
            if self._matches_filters(problem, filters):
                filtered_problems.append(problem)
        
        return filtered_problems
    
    def _matches_filters(self, problem, filters):
        """Check if a problem matches the given filters."""
        # Rating filter
        if 'rating_range' in filters:
            min_rating, max_rating = filters['rating_range']
            if not (min_rating <= problem['rating'] <= max_rating):
                return False
        
        # Tag_and filter
        if 'tag_and' in filters and filters['tag_and']:
            if not all(tag in problem['tags'] for tag in filters['tag_and']):
                return False
        
        # Tag_or filter
        if 'tag_or' in filters and filters['tag_or']:
            if not any(tag in problem['tags'] for tag in filters['tag_or']):
                return False
        
        # Time filter
        if 'time_range' in filters:
            start_time, end_time = filters['time_range']
            if not (start_time <= problem['submission_time'] <= end_time):
                return False
        
        # Contest ID filter
        if 'contest_id' in filters:
            if str(problem['contest_id']) != str(filters['contest_id']):
                return False
        
        # Problem ID filter
        if 'problem_id' in filters:
            if problem['problem_id'] != filters['problem_id']:
                return False
        
        return True
