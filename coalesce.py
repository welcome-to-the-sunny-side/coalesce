import click
from src import cf_api, data_manager
import json # Added for cf_api.py potential JSONDecodeError import
from src.utils import parse_date_range_input, render_problems_table # For list command
from datetime import datetime # For list command time filtering
import random # For gimme command

@click.group()
def cli():
    """Coalesce: Your Codeforces Problem Companion"""
    data_manager.ensure_data_dir_exists() # Ensure data directory and subdirectories exist on startup

@cli.command("help")
@click.pass_context
def show_help(ctx):
    """Shows a list of all commands and their descriptions."""
    click.echo(cli.get_help(ctx))

@cli.command("pull")
def pull():
    """Refreshes the JSON file with solved problems from configured handles."""
    handles = data_manager.load_handles()
    if not handles:
        click.echo("No handles configured. Use 'coalesce add <handle>' to add one.")
        return
    
    click.echo(f"Fetching solved problems for: {', '.join(handles)}")
    try:
        all_solved = cf_api.get_all_solved_problems(handles)
        data_manager.save_solved_problems_data(all_solved)
        click.echo(f"Successfully updated {data_manager.SOLVED_PROBLEMS_FILE} with {len(all_solved)} problems.")
    except Exception as e:
        click.echo(f"An error occurred during the pull operation: {e}")

@cli.command("add")
@click.argument('handle')
def add(handle):
    """Adds a Codeforces handle to the list and refreshes solved problems."""
    if data_manager.add_handle(handle):
        click.echo(f"Added handle: {handle}")
        click.echo("Refreshing solved problems data...")
        # Automatically call pull after adding a handle
        ctx = click.get_current_context()
        ctx.invoke(pull)
    else:
        click.echo(f"Handle {handle} already exists.")

@cli.command("remove")
@click.argument('handle')
def remove(handle):
    """Removes a Codeforces handle from the list and refreshes solved problems."""
    if data_manager.remove_handle(handle):
        click.echo(f"Removed handle: {handle}")
        click.echo("Refreshing solved problems data...")
        # Automatically call pull after removing a handle
        ctx = click.get_current_context()
        ctx.invoke(pull)
    else:
        click.echo(f"Handle {handle} not found.")

@cli.command("whoami")
def whoami():
    """Shows the list of configured Codeforces handles."""
    handles = data_manager.load_handles()
    if handles:
        click.echo("Configured handles:")
        for handle in handles:
            click.echo(f"- {handle}")
    else:
        click.echo("No handles configured. Use 'coalesce add <handle>' to add one.")

@cli.command("list")
@click.option('--rating', default="0-3500", help="Filter by rating range e.g., '1000-1500'. Default: 0-3500.")
@click.option('--tag_and', help="Filter by problems having ALL specified tags (comma-separated). e.g., 'dp,graphs'")
@click.option('--tag_or', help="Filter by problems having AT LEAST ONE of the specified tags (comma-separated). e.g., 'implementation,strings'")
@click.option('--time', 'time_param', help="Filter by solved time. Accepts 'dd/mm/yyyy-dd/mm/yyyy' or natural language like 'today', 'last week'.")
@click.option('--cid', help="Filter by contest ID.")
@click.option('--pid', help="Filter by problem ID (index within contest, e.g., A, B1). Works best with --cid.")
def list_problems(rating, tag_and, tag_or, time_param, cid, pid):
    """Lists solved problems based on specified criteria."""
    solved_problems = data_manager.load_solved_problems_data()
    if not solved_problems:
        click.echo("No solved problems data found. Try 'coalesce pull' first.")
        return

    filtered_problems = solved_problems

    # 1. Rating filter
    try:
        min_rating_str, max_rating_str = rating.split('-')
        min_r, max_r = int(min_rating_str), int(max_rating_str)
        filtered_problems = [p for p in filtered_problems if p.get('Rating') is not None and min_r <= p['Rating'] <= max_r]
    except ValueError:
        click.echo(f"Invalid rating format: '{rating}'. Please use 'min-max'.")
        return

    # 2. Tag_and filter
    if tag_and:
        required_tags = {t.strip().lower() for t in tag_and.split(',')}
        filtered_problems = [
            p for p in filtered_problems 
            if required_tags.issubset({tag.lower() for tag in p.get('Tags', [])})
        ]

    # 3. Tag_or filter
    if tag_or:
        desired_tags = {t.strip().lower() for t in tag_or.split(',')}
        filtered_problems = [
            p for p in filtered_problems
            if any(tag.lower() in desired_tags for tag in p.get('Tags', []))
        ]

    # 4. Time filter
    if time_param:
        start_date, end_date = parse_date_range_input(time_param)
        if start_date and end_date:
            # Convert submission times from Unix timestamp to datetime objects for comparison
            temp_problems = []
            for p in filtered_problems:
                submission_unix_time = p.get('Submission Time')
                if submission_unix_time is not None:
                    try:
                        submission_dt = datetime.fromtimestamp(submission_unix_time)
                        if start_date <= submission_dt <= end_date:
                            temp_problems.append(p)
                    except (TypeError, ValueError):
                        pass # Ignore problems with invalid submission times
            filtered_problems = temp_problems
        else:
            click.echo(f"Could not parse time parameter: '{time_param}'.")
            # Optionally, one might choose to return or continue without time filtering

    # 5. Contest ID (cid) filter
    if cid:
        # Problem Identifier is like "<contestId><problemIndex>"
        # We need to ensure cid is a string for comparison with the start of Problem Identifier
        cid_str = str(cid) 
        filtered_problems = [p for p in filtered_problems if str(p.get("Problem Identifier", "")).startswith(cid_str)]
        # This might be too broad if a contest ID is a prefix of another (e.g., 17 vs 170). 
        # A more robust way if contestId was a separate field: [p for p in filtered_problems if str(p.get('contestId')) == cid_str]
        # Given current structure, this is a direct interpretation. 
        # To be more precise, we'd need to parse Problem Identifier or ensure contestId is stored separately.
        # For now, we assume `problem['contestId']` was correctly captured if it was part of the problem object from user.status
        # Let's refine this: the problem object from API does have 'contestId'. If we ensure it's stored, filtering is cleaner.
        # Assuming 'Contest ID' (or similar) could be a key if added during data fetching from problem object.
        # For now, sticking to Problem Identifier structure as per earlier data shape.
        # A better approach would be to check `p['Problem Identifier']` starts with `cid` AND the character after `cid` is not a digit.
        
        # Revised CID filter for better accuracy with Problem Identifier structure
        def check_cid(problem_identifier, contest_id_str):
            if not problem_identifier.startswith(contest_id_str):
                return False
            # Check if the part after contest_id_str is not a digit (i.e., it's the problem index like 'A', 'B1')
            if len(problem_identifier) > len(contest_id_str):
                return not problem_identifier[len(contest_id_str)].isdigit()
            return True # Exact match like '1700' if problem index is empty (unlikely for CF)

        filtered_problems = [p for p in filtered_problems if check_cid(str(p.get("Problem Identifier", "")), cid_str)]

    # 6. Problem ID (pid) filter
    if pid:
        # Problem Identifier is like "<contestId><problemIndex>"
        # This filter is most effective when --cid is also used.
        pid_str = str(pid).upper() # Problem indices are usually uppercase letters or letter+digit
        if cid: # If contest ID is specified, match exact problem
            target_problem_identifier = str(cid) + pid_str
            filtered_problems = [p for p in filtered_problems if p.get("Problem Identifier", "").upper() == target_problem_identifier]
        else: # If only pid is given, match any problem ending with this index
            filtered_problems = [p for p in filtered_problems if p.get("Problem Identifier", "").upper().endswith(pid_str)]

    render_problems_table(filtered_problems)

@cli.command("gimme")
@click.option('--spoil', is_flag=True, default=False, help="Print problem rating and tags.")
@click.option('--rating', 'rating_range_str', default="0-3500", help="Restrict problem rating to [x, y]. Default: 0-3500.")
@click.option('--tag_and', 'tag_and_str', help="Return a problem with ALL specified tags (comma-separated).")
@click.option('--tag_or', 'tag_or_str', help="Return a problem with AT LEAST ONE of the specified tags (comma-separated).")
@click.option('--solved', 'include_solved', is_flag=True, default=False, help="Include problems already solved by the user. Default: false.")
def gimme_problem(spoil, rating_range_str, tag_and_str, tag_or_str, include_solved):
    """Suggests a random problem based on specified criteria."""
    click.echo("Fetching the entire Codeforces problemset. This may take a moment...")
    all_cf_problems = cf_api.get_all_problemset_problems()
    if not all_cf_problems:
        click.echo("Could not fetch problemset from Codeforces. Please check your connection or try again later.")
        return

    user_solved_problems_data = data_manager.load_solved_problems_data()
    user_solved_ids = {p["Problem Identifier"] for p in user_solved_problems_data}

    candidate_problems = all_cf_problems

    # 1. Filter by --solved status (unless include_solved is True)
    if not include_solved:
        candidate_problems = [
            p for p in candidate_problems 
            if f"{p.get('contestId')}{p.get('index')}" not in user_solved_ids
        ]

    # 2. Filter by rating
    try:
        min_rating_str, max_rating_str = rating_range_str.split('-')
        min_r, max_r = int(min_rating_str), int(max_rating_str)
        candidate_problems = [p for p in candidate_problems if p.get('rating') is not None and min_r <= p['rating'] <= max_r]
    except ValueError:
        click.echo(f"Invalid rating format: '{rating_range_str}'. Please use 'min-max'.")
        return

    # 3. Filter by tag_and
    if tag_and_str:
        required_tags = {t.strip().lower() for t in tag_and_str.split(',') if t.strip()}
        if required_tags:
            candidate_problems = [
                p for p in candidate_problems 
                if required_tags.issubset({tag.lower() for tag in p.get('tags', [])})
            ]

    # 4. Filter by tag_or
    if tag_or_str:
        any_of_tags = {t.strip().lower() for t in tag_or_str.split(',') if t.strip()}
        if any_of_tags:
            candidate_problems = [
                p for p in candidate_problems
                if any(tag.lower() in any_of_tags for tag in p.get('tags', []))
            ]
    
    if not candidate_problems:
        click.echo("No problems found matching your criteria.")
        return

    selected_problem = random.choice(candidate_problems)

    problem_identifier = f"{selected_problem.get('contestId')}{selected_problem.get('index')}"
    problem_link = f"https://codeforces.com/problemset/problem/{selected_problem.get('contestId')}/{selected_problem.get('index')}"
    
    click.echo(f"Here's a problem for you:")
    click.echo(f"Problem: {selected_problem.get('name')} ({problem_identifier})")
    click.echo(f"Link: {problem_link}")

    if spoil:
        rating_val = selected_problem.get('rating', 'N/A')
        tags_list = selected_problem.get('tags', [])
        tags_val = ', '.join(tags_list) if tags_list else 'N/A'
        click.echo(f"Rating: {rating_val}")
        click.echo(f"Tags: {tags_val}")

@cli.command("export")
def export_data():
    """Exports the central solved problems data (JSON) to standard output."""
    solved_problems_data = data_manager.load_solved_problems_data()
    if not solved_problems_data:
        click.echo("No solved problems data to export. Run 'coalesce pull' first.", err=True)
        return
    
    # Pretty print JSON to stdout
    click.echo(json.dumps(solved_problems_data, indent=4))

if __name__ == '__main__':
    cli()
