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
        self.all_problems_file = os.path.join(self.config_dir, "all_problems.json")
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.backup_dir = os.path.join(self.config_dir, "backups")
        self.handles_file = os.path.join(self.config_dir, "handles.json")  # Keep for backward compatibility
        
        # Create config directory and files if they don't exist
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        if not os.path.exists(self.data_file):
            self._write_json(self.data_file, {"last_refresh": 0, "problems": {}})
            
        if not os.path.exists(self.all_problems_file):
            self._write_json(self.all_problems_file, {
                "last_refresh": 0,
                "problems": []
            })
            
        # Create or load configuration file
        if not os.path.exists(self.config_file):
            # Default configuration
            self._write_json(self.config_file, {
                "auto_refresh": {
                    "enabled": True,
                    "period_days": 1
                },
                "handles": []
            })
        
        # Load configuration
        self.config = self._read_json(self.config_file)
        
        # Migrate handles from old file to config if needed
        if os.path.exists(self.handles_file):
            try:
                handles_data = self._read_json(self.handles_file)
                old_handles = handles_data.get("handles", [])
                
                # If there are handles in the old file and none in the config
                if old_handles and not self.config.get("handles"):
                    self.config["handles"] = old_handles
                    self._write_json(self.config_file, self.config)
                    # Could remove old file, but keeping for backup
            except Exception as e:
                print(f"Warning: Error migrating handles: {str(e)}")
    
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
        return self.config.get("handles", [])
    
    def add_handle(self, handle):
        """Add a handle to the list."""
        handles = self.config.get("handles", [])
        
        if handle in handles:
            return False, f"Handle '{handle}' already exists"
        
        # Validate the handle exists on Codeforces
        url = f"https://codeforces.com/api/user.info?handles={handle}"
        response = requests.get(url)
        data = response.json()
        
        if data['status'] != 'OK':
            return False, f"Failed to validate handle '{handle}': {data.get('comment', 'Unknown error')}"
        
        handles.append(handle)
        self.config["handles"] = handles
        self._write_json(self.config_file, self.config)
        return True, f"Added handle '{handle}'"
    
    def remove_handle(self, handle):
        """Remove a handle from the list."""
        handles = self.config.get("handles", [])
        
        if handle not in handles:
            return False, f"Handle '{handle}' does not exist"
        
        handles.remove(handle)
        self.config["handles"] = handles
        self._write_json(self.config_file, self.config)
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
    
    def lazy_refresh(self):
        """Refresh both data files if they're older than the configured period."""
        # Check if auto-refresh is enabled
        auto_refresh = self.config.get("auto_refresh", {"enabled": True, "period_days": 1})
        if not auto_refresh.get("enabled", True):
            return  # Auto-refresh is disabled
        
        # Get the configured period in days
        period_days = auto_refresh.get("period_days", 1)
        period_seconds = period_days * 24 * 60 * 60
        current_time = int(time.time())
        
        # Skip refresh if period is set to 0 (manual refresh only)
        if period_days <= 0:
            return
        
        # Refresh solved problems if needed
        try:
            data = self._read_json(self.data_file)
            last_refresh = data.get("last_refresh", 0)
            if current_time - last_refresh > period_seconds:
                print(f"Refreshing solved problems data (last refresh was over {period_days} day(s) ago)...")
                self.update_problems_data(silent=True)
        except Exception as e:
            print(f"Warning: Error during lazy refresh of solved problems: {str(e)}")
        
        # Refresh all problems if needed
        try:
            all_problems_data = self._read_json(self.all_problems_file)
            last_refresh = all_problems_data.get("last_refresh", 0)
            if current_time - last_refresh > period_seconds:
                print(f"Refreshing all Codeforces problems data (last refresh was over {period_days} day(s) ago)...")
                self.get_all_problems(force_refresh=True, silent=True)
        except Exception as e:
            print(f"Warning: Error during lazy refresh of all problems: {str(e)}")
    
    def update_problems_data(self, silent=False):
        """Update the central JSON file with problems from all handles.
        
        Args:
            silent: If True, suppress progress messages.
            
        Returns:
            A tuple (success, message).
        """
        start_time = time.time()
        handles = self.get_handles()
        
        if not handles:
            return False, "No handles found. Add handles using 'coalesce add <handle>'"
        
        # Create a backup before updating
        self.backup_data()
        
        all_problems = {}
        for handle in handles:
            if not silent:
                print(f"Fetching data for handle: {handle}...")
            success, result = self.get_solved_problems(handle)
            if success:
                all_problems.update(result)
            else:
                if not silent:
                    print(f"Warning: {result}")
        
        # Write to the central JSON file with last refresh timestamp
        data = {
            "last_refresh": int(time.time()),
            "problems": all_problems
        }
        self._write_json(self.data_file, data)
        
        # Calculate elapsed time
        elapsed = time.time() - start_time
        
        return True, f"Updated solve cache with {len(all_problems)} problems in {elapsed:.2f} seconds"
    
    def get_problems(self, filters=None):
        """Get problems based on filters."""
        if not os.path.exists(self.data_file):
            return []
        
        data = self._read_json(self.data_file)
        problems = data.get("problems", data)  # Handle both new and old format
        
        if not filters:
            return list(problems.values())
        
        filtered_problems = []
        for problem in problems.values():
            if self._matches_filters(problem, filters):
                filtered_problems.append(problem)
        
        return filtered_problems
    
    def get_config(self):
        """Get the current configuration."""
        return self.config
    
    def update_config(self, new_config):
        """Update the configuration file.
        
        Args:
            new_config: The new configuration dictionary to merge with existing config.
            
        Returns:
            The updated configuration.
        """
        # Merge new config with existing config
        self.config.update(new_config)
        self._write_json(self.config_file, self.config)
        return self.config
    
    def set_auto_refresh(self, enabled=True, period_days=1):
        """Set the auto-refresh configuration.
        
        Args:
            enabled: Whether auto-refresh is enabled.
            period_days: Auto-refresh period in days (0 for manual refresh only).
            
        Returns:
            A tuple (success, message).
        """
        # Validate period_days
        try:
            period_days = float(period_days)
            if period_days < 0:
                return False, "Period must be a non-negative number"
        except ValueError:
            return False, "Period must be a number"
        
        # Update configuration
        self.config["auto_refresh"] = {
            "enabled": bool(enabled),
            "period_days": period_days
        }
        
        # Save to file
        self._write_json(self.config_file, self.config)
        
        if not enabled:
            return True, "Auto-refresh disabled"
        elif period_days == 0:
            return True, "Auto-refresh set to manual only"
        else:
            return True, f"Auto-refresh enabled with period of {period_days} day(s)"
    
    def get_all_problems(self, force_refresh=False, silent=False):
        """Get all Codeforces problems with caching mechanism.

        Args:
            force_refresh: If True, force a refresh regardless of the last refresh time.
            silent: If True, suppress warning messages.

        Returns:
            Tuple of (problems list, message) where message describes the operation result.
        """
        start_time = int(time.time())
        current_time = start_time
        one_day_in_seconds = 24 * 60 * 60
        
        # Load the cached data
        all_problems_data = self._read_json(self.all_problems_file)
        last_refresh = all_problems_data.get("last_refresh", 0)
        
        # Check if we need to refresh the data
        if force_refresh or (current_time - last_refresh > one_day_in_seconds):
            try:
                if not silent:
                    print("Fetching all problems from Codeforces API...")
                    
                # Make API request to get all problems
                url = "https://codeforces.com/api/problemset.problems"
                response = requests.get(url)
                data = response.json()
                
                if data["status"] != "OK":
                    # Return cached data in case of API failure
                    if not silent:
                        print("Failed to fetch problems from Codeforces API, using cached data.")
                    cached_problems = all_problems_data.get("problems", [])
                    return cached_problems, f"Using cached data ({len(cached_problems)} problems)"
                    
                # Process and store the problems
                problems = []
                for problem in data["result"]["problems"]:
                    if "contestId" not in problem or "index" not in problem:
                        continue
                        
                    problem_id = f"{problem['contestId']}{problem['index']}"
                    rating = problem.get("rating", 0)
                    tags = problem.get("tags", [])
                    
                    problem_link = f"https://codeforces.com/problemset/problem/{problem['contestId']}/{problem['index']}"
                    problems.append({
                        "problem_id": problem_id,
                        "problem_link": problem_link,
                        "rating": rating,
                        "tags": tags,
                        "contest_id": problem['contestId'],
                        "problem_code": problem['index']
                    })
                
                # Update the cache
                all_problems_data = {
                    "last_refresh": current_time,
                    "problems": problems
                }
                self._write_json(self.all_problems_file, all_problems_data)
                
                # Calculation elapsed time
                elapsed = time.time() - start_time
                
                # if not silent:
                    # print(f"Successfully cached {len(problems)} problems from Codeforces.")
                return problems, f"Updated exhaustive problem cache with {len(problems)} problems in {elapsed:.2f} seconds"
                
            except Exception as e:
                # Return cached data in case of any error
                if not silent:
                    print(f"Error fetching problems from Codeforces API: {str(e)}")
                cached_problems = all_problems_data.get("problems", [])
                return cached_problems, f"Error occurred, using cached data ({len(cached_problems)} problems)"
        else:
            # Return cached data if it's fresh enough
            cached_problems = all_problems_data.get("problems", [])
            return cached_problems, f"Using cached data ({len(cached_problems)} problems, last update: {datetime.fromtimestamp(last_refresh).strftime('%Y-%m-%d %H:%M:%S')})"
    
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
            if 'submission_time' in problem and not (start_time <= problem['submission_time'] <= end_time):
                return False
        
        # Contest ID filter
        if 'contest_id' in filters:
            if str(problem.get('contest_id', '')) != str(filters['contest_id']):
                return False
        
        # Problem ID filter
        if 'problem_id' in filters:
            if problem['problem_id'] != filters['problem_id']:
                return False
        
        # Contest ID range filter
        if 'cid_range' in filters and filters['cid_range'] is not None:
            min_cid, max_cid = filters['cid_range']
            contest_id = problem.get('contest_id', 0)
            if not (min_cid <= contest_id <= max_cid):
                return False
        
        return True
