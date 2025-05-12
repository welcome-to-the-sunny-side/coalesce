import requests
import time
import json

API_BASE_URL = "https://codeforces.com/api"

def get_solved_for_handle(handle):
    """Fetches solved problems for a single Codeforces handle."""
    url = f"{API_BASE_URL}/user.status?handle={handle}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
    except requests.RequestException as e:
        print(f"Error fetching data for {handle}: {e}")
        return []
    except json.JSONDecodeError:
        print(f"Error decoding JSON for {handle}. Response: {response.text[:200]}...") # Log part of response
        return []

    if data.get('status') != 'OK':
        print(f"API error for {handle}: {data.get('comment', 'No comment')}")
        return []

    solved_problems_list = []
    if 'result' not in data or not isinstance(data['result'], list):
        print(f"Unexpected data structure for {handle}: 'result' field missing or not a list.")
        return []

    for item in data['result']:
        if item.get('verdict') == 'OK':
            problem = item.get('problem')
            if not problem or not isinstance(problem, dict):
                # Skip if problem data is missing or malformed
                continue

            contest_id = problem.get('contestId')
            problem_index = problem.get('index')

            # Skip if essential problem identifiers are missing
            if contest_id is None or problem_index is None:
                continue
            
            # Ensure contest_id is treated as string for concatenation if it's an int
            contest_id_str = str(contest_id)

            problem_identifier = f"{contest_id_str}{problem_index}"
            problem_link = f"https://codeforces.com/problemset/problem/{contest_id_str}/{problem_index}"
            
            submission_id = item.get('id')
            if submission_id is None:
                continue # Skip if submission ID is missing
            
            submission_link = f"https://codeforces.com/contest/{contest_id_str}/submission/{submission_id}"
            
            # Use item's creationTimeSeconds for submission time
            submission_time_unix = item.get('creationTimeSeconds')

            problem_entry = {
                "Problem Identifier": problem_identifier,
                "Problem Link": problem_link,
                "Rating": problem.get('rating'), # Can be None if not rated
                "Tags": problem.get('tags', []),
                "Submission ID": submission_id,
                "Link to Submission": submission_link,
                "Submission Time": submission_time_unix # Unix timestamp
            }
            solved_problems_list.append(problem_entry)
    return solved_problems_list

def get_all_solved_problems(handles):
    """Aggregates unique solved problems from a list of handles."""
    all_problems_dict = {}
    for i, handle in enumerate(handles):
        if i > 0:
            time.sleep(1) # Basic rate limiting to be polite to the API
        print(f"Fetching solved problems for {handle}...")
        problems = get_solved_for_handle(handle)
        for p in problems:
            # Use Problem Identifier to ensure uniqueness
            # If multiple alts solved the same problem, this keeps the first one encountered.
            # Could be modified to keep the earliest/latest submission if needed.
            if p["Problem Identifier"] not in all_problems_dict:
                all_problems_dict[p["Problem Identifier"]] = p
    return list(all_problems_dict.values())

def get_all_problemset_problems():
    """Fetches the entire problemset from Codeforces."""
    url = f"{API_BASE_URL}/problemset.problems"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"Error fetching problemset: {e}")
        return []
    except json.JSONDecodeError:
        print(f"Error decoding JSON for problemset. Response: {response.text[:200]}...")
        return []

    if data.get('status') != 'OK':
        print(f"API error for problemset: {data.get('comment', 'No comment')}")
        return []

    problemset = []
    if 'result' in data and 'problems' in data['result'] and isinstance(data['result']['problems'], list):
        for p_info in data['result']['problems']:
            # Ensure essential fields are present for 'gimme' command usage
            if p_info.get('contestId') is not None and p_info.get('index') is not None and p_info.get('name') is not None:
                 problemset.append({
                    "contestId": p_info.get('contestId'),
                    "index": p_info.get('index'),
                    "name": p_info.get('name'),
                    "rating": p_info.get('rating'), # Can be None
                    "tags": p_info.get('tags', [])
                })
    else:
        print("Unexpected data structure for problemset: 'result.problems' field missing or not a list.")

    return problemset
