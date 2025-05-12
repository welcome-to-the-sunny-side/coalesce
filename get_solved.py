import requests
import csv

def get_solved_problems(handle):
    url = f"https://codeforces.com/api/user.status?handle={handle}"
    response = requests.get(url)
    data = response.json()

    if data['status'] != 'OK':
        print(f"Failed to fetch data for {handle}: {data['comment']}")
        return []

    solved_problems = []
    for item in data['result']:
        if item['verdict'] == 'OK':
            problem = item['problem']
            submission_id = item['id']
            contest_id = problem['contestId']
            problem_code = problem['index']
            rating = problem.get('rating', 0)  # Fallback to 0 if rating not available
            tags = problem.get('tags', [])  # Fetch tags
            submissionTime= problem.get('creationTimeSeconds') # in UNIX format
            
            if rating >= x:  # Only include problems with rating >= x
                problem_id = f"{contest_id}{problem_code}"  # Combine contest ID and problem index
                solved_problems.append((problem_id, contest_id, problem_code, rating, tags, submission_id, submissionTime))

    return solved_problems

def merge_solved_problems(handles, min_rating):
    merged_problems = {}
    
    for handle in handles:
        problems = get_solved_problems(handle)
        for problem_id, contest_id, problem_code, rating, tags, submission_id, submissionTime in problems:
            if problem_id not in merged_problems:  # Avoid duplicates
                merged_problems[problem_id] = (contest_id, problem_code, rating, tags, submission_id, submissionTime)

    return merged_problems

def save_to_csv(merged_results, filename='solved.csv'):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(['Problem Identifier', 'Problem Link' ,'Rating', 'Tags', 'Submission ID', 'Link to Submission', 'Submission Time'])
        for problem_id, (contest_id, problem_code, rating, tags, submission_id, submissionTime) in merged_results.items():
            tags_str = ', '.join(tags)  # Convert list of tags to a string
            problem_link = f"https://codeforces.com/problemset/problem/{contest_id}/{problem_code}"
            submission_link = f"https://codeforces.com/contest/{problem_id[:-1]}/submission/{submission_id}"  # Create the link
            writer.writerow([problem_id, problem_link, rating, tags_str, submission_id, submission_link, submissionTime])

# Example usage:
handles = []  # Replace with your list of handles
x = 800  # x will always be 800
merged_results = merge_solved_problems(handles, x)

save_to_csv(merged_results, 'solved.csv')

print("Results have been written to solved.csv")
