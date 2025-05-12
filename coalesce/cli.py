"""
Command-line interface for coalesce.
"""

import click
import json
import random
import sys
import time
from datetime import datetime, timedelta
from tabulate import tabulate

from .data_manager import DataManager


def parse_time_parameter(time_param):
    """Parse time parameter into Unix timestamps."""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Natural language time expressions
    if time_param == "today":
        start_time = int(today.timestamp())
        end_time = int((today + timedelta(days=1)).timestamp()) - 1
    elif time_param == "yesterday":
        start_time = int((today - timedelta(days=1)).timestamp())
        end_time = int(today.timestamp()) - 1
    elif time_param == "this week":
        start_of_week = today - timedelta(days=today.weekday())
        start_time = int(start_of_week.timestamp())
        end_time = int(time.time())
    elif time_param == "last week":
        start_of_this_week = today - timedelta(days=today.weekday())
        start_of_last_week = start_of_this_week - timedelta(days=7)
        end_of_last_week = start_of_this_week - timedelta(seconds=1)
        start_time = int(start_of_last_week.timestamp())
        end_time = int(end_of_last_week.timestamp())
    elif time_param == "this month":
        start_of_month = today.replace(day=1)
        start_time = int(start_of_month.timestamp())
        end_time = int(time.time())
    elif time_param == "last month":
        start_of_this_month = today.replace(day=1)
        last_month = start_of_this_month - timedelta(days=1)
        start_of_last_month = last_month.replace(day=1)
        end_of_last_month = start_of_this_month - timedelta(seconds=1)
        start_time = int(start_of_last_month.timestamp())
        end_time = int(end_of_last_month.timestamp())
    elif time_param == "this year":
        start_of_year = today.replace(month=1, day=1)
        start_time = int(start_of_year.timestamp())
        end_time = int(time.time())
    elif time_param == "last year":
        start_of_this_year = today.replace(month=1, day=1)
        last_year = start_of_this_year.replace(year=today.year-1)
        end_of_last_year = start_of_this_year - timedelta(seconds=1)
        start_time = int(last_year.timestamp())
        end_time = int(end_of_last_year.timestamp())
    # Date range in format dd/mm/yyyy-dd/mm/yyyy
    elif "-" in time_param:
        try:
            start_date_str, end_date_str = time_param.split("-")
            start_date = datetime.strptime(start_date_str, "%d/%m/%Y")
            end_date = datetime.strptime(end_date_str, "%d/%m/%Y").replace(hour=23, minute=59, second=59)
            start_time = int(start_date.timestamp())
            end_time = int(end_date.timestamp())
        except ValueError:
            raise click.BadParameter("Date range format should be DD/MM/YYYY-DD/MM/YYYY")
    else:
        raise click.BadParameter("Invalid time parameter")
    
    return start_time, end_time


def parse_rating_range(rating_range):
    """Parse rating range parameter."""
    try:
        if not rating_range:
            return 0, 3500
        
        if "-" not in rating_range:
            raise ValueError("Rating range must be in format x-y")
        
        min_rating, max_rating = map(int, rating_range.split("-"))
        return min_rating, max_rating
    except ValueError as e:
        raise click.BadParameter(str(e))


def parse_cid_range(cid_range):
    """Parse contest ID range parameter."""
    try:
        if not cid_range:
            return None
        
        if "-" not in cid_range:
            raise ValueError("Contest ID range must be in format x-y")
        
        min_cid, max_cid = map(int, cid_range.split("-"))
        return min_cid, max_cid
    except ValueError as e:
        raise click.BadParameter(str(e))


def parse_tags(tags_str):
    """Parse tags parameter."""
    if not tags_str:
        return []
    
    return [tag.strip() for tag in tags_str.split(",")]


@click.group()
def cli():
    """Coalesce - Track and analyze your Codeforces problem-solving data."""
    pass


@cli.command()
def help():
    """Show all available commands and their descriptions."""
    ctx = click.Context(cli)
    click.echo(cli.get_help(ctx))


@cli.command()
def pull():
    """Refresh the central JSON file with the latest problems."""
    data_manager = DataManager()
    success, message = data_manager.update_problems_data()
    
    if success:
        click.secho(message, fg="green")
    else:
        click.secho(message, fg="red")


@cli.command()
@click.argument("handle")
def add(handle):
    """Add a Codeforces handle to track."""
    data_manager = DataManager()
    success, message = data_manager.add_handle(handle)
    
    if success:
        click.secho(message, fg="green")
        # Automatically update problems data
        click.echo("Updating problems data...")
        data_manager.update_problems_data()
    else:
        click.secho(message, fg="red")


@cli.command()
@click.argument("handle")
def remove(handle):
    """Remove a Codeforces handle from tracking."""
    data_manager = DataManager()
    success, message = data_manager.remove_handle(handle)
    
    if success:
        click.secho(message, fg="green")
        # Automatically update problems data
        click.echo("Updating problems data...")
        data_manager.update_problems_data()
    else:
        click.secho(message, fg="red")


@cli.command()
def whoami():
    """Show the list of tracked Codeforces handles."""
    data_manager = DataManager()
    handles = data_manager.get_handles()
    
    if handles:
        click.echo("Tracked handles:")
        for handle in handles:
            click.echo(f"- {handle}")
    else:
        click.echo("No handles being tracked. Add handles using 'coalesce add <handle>'")


@cli.command()
@click.option("--spoil", is_flag=True, help="Show problem rating and tags")
@click.option("--rating", help="Rating range (format: x-y, default: 0-3500)")
@click.option("--tag_and", help="Problem must have ALL these tags (comma-separated)")
@click.option("--tag_or", help="Problem must have AT LEAST ONE of these tags (comma-separated)")
@click.option("--cid", help="Contest ID range (format: x-y)")
@click.option("--solved", is_flag=True, help="Include problems that are already solved")
def gimme(spoil, rating, tag_and, tag_or, cid, solved):
    """Get a random problem matching the given criteria."""
    data_manager = DataManager()
    
    # Parse filters
    filters = {}
    if rating:
        filters["rating_range"] = parse_rating_range(rating)
    else:
        filters["rating_range"] = (0, 3500)
    
    if tag_and:
        filters["tag_and"] = parse_tags(tag_and)
    
    if tag_or:
        filters["tag_or"] = parse_tags(tag_or)
        
    if cid:
        filters["cid_range"] = parse_cid_range(cid)
    
    # Get problems (either all problems from API or just solved ones)
    if solved:
        problems = data_manager.get_problems(filters)
    else:
        # For unsolved problems, we need to fetch all problems and filter out solved ones
        all_problems_url = "https://codeforces.com/api/problemset.problems"
        import requests
        response = requests.get(all_problems_url)
        data = response.json()
        
        if data["status"] != "OK":
            click.secho(f"Failed to fetch problems: {data.get('comment', 'Unknown error')}", fg="red")
            return
        
        # Get list of solved problem IDs
        solved_problems = data_manager.get_problems()
        solved_ids = {p["problem_id"] for p in solved_problems}
        
        # Filter unsolved problems
        unsolved_problems = []
        for problem in data["result"]["problems"]:
            if "contestId" not in problem or "index" not in problem:
                continue
                
            problem_id = f"{problem['contestId']}{problem['index']}"
            
            # Skip if already solved
            if problem_id in solved_ids:
                continue
            
            rating = problem.get("rating", 0)
            tags = problem.get("tags", [])
            
            # Apply rating filter
            min_rating, max_rating = filters["rating_range"]
            if not (min_rating <= rating <= max_rating):
                continue
            
            # Apply tag_and filter
            if "tag_and" in filters and filters["tag_and"]:
                if not all(tag in tags for tag in filters["tag_and"]):
                    continue
            
            # Apply tag_or filter
            if "tag_or" in filters and filters["tag_or"]:
                if not any(tag in tags for tag in filters["tag_or"]):
                    continue
                    
            # Apply contest ID range filter
            if "cid_range" in filters:
                min_cid, max_cid = filters["cid_range"]
                contest_id = problem.get("contestId", 0)
                if not (min_cid <= contest_id <= max_cid):
                    continue
            
            problem_link = f"https://codeforces.com/problemset/problem/{problem['contestId']}/{problem['index']}"
            unsolved_problems.append({
                "problem_id": problem_id,
                "problem_link": problem_link,
                "rating": rating,
                "tags": tags
            })
        
        problems = unsolved_problems
    
    if not problems:
        click.secho("No problems found matching the criteria", fg="yellow")
        return
    
    # Select a random problem
    problem = random.choice(problems)
    
    # Display the problem
    click.echo(f"{problem['problem_id']} {problem['problem_link']}")
    
    if spoil:
        rating = problem.get("rating", "Unknown")
        tags = ", ".join(problem.get("tags", []))
        click.echo(f"Rating: {rating}")
        click.echo(f"Tags: {tags}")


@cli.command()
@click.option("--rating", help="Rating range (format: x-y, default: 0-3500)")
@click.option("--tag_and", help="Problem must have ALL these tags (comma-separated)")
@click.option("--tag_or", help="Problem must have AT LEAST ONE of these tags (comma-separated)")
@click.option("--time", help="Time range (format: DD/MM/YYYY-DD/MM/YYYY or keywords)")
@click.option("--cid", help="Contest ID")
@click.option("--pid", help="Problem ID")
def list(rating, tag_and, tag_or, time, cid, pid):
    """List problems matching the given criteria."""
    data_manager = DataManager()
    
    # Parse filters
    filters = {}
    if rating:
        filters["rating_range"] = parse_rating_range(rating)
    else:
        filters["rating_range"] = (0, 3500)
    
    if tag_and:
        filters["tag_and"] = parse_tags(tag_and)
    
    if tag_or:
        filters["tag_or"] = parse_tags(tag_or)
    
    if time:
        filters["time_range"] = parse_time_parameter(time)
    
    if cid:
        filters["contest_id"] = cid
    
    if pid:
        filters["problem_id"] = pid
    
    # Get problems
    problems = data_manager.get_problems(filters)
    
    if not problems:
        click.secho("No problems found matching the criteria", fg="yellow")
        return
    
    # Prepare the data for display
    table_data = []
    for problem in problems:
        submission_time = datetime.fromtimestamp(problem["submission_time"]).strftime("%Y-%m-%d %H:%M:%S")
        tags = ", ".join(problem["tags"][:3])  # Show only first 3 tags to save space
        if len(problem["tags"]) > 3:
            tags += "..."
            
        # Truncate URLs to avoid table overflow
        problem_link = problem["problem_link"]
        if len(problem_link) > 40:
            problem_link = problem_link[:37] + "..."
            
        submission_link = problem["submission_link"]
        if len(submission_link) > 40:
            submission_link = submission_link[:37] + "..."
        
        table_data.append([
            problem["problem_id"],
            problem_link,
            problem["rating"],
            tags,
            problem["submission_id"],
            submission_link,
            submission_time
        ])
    
    # Display the table with maximal column widths
    headers = ["Problem ID", "Problem Link", "Rating", "Tags", "Submission ID", "Submission Link", "Submission Time"]
    # Set max column widths to prevent table overflow
    click.echo(tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[15, 40, 8, 25, 15, 40, 20]))
    click.echo(f"Total problems: {len(problems)}")


@cli.command()
def export():
    """Export the problem data to a CSV file."""
    data_manager = DataManager()
    problems = data_manager.get_problems()
    
    if not problems:
        click.secho("No problems found to export", fg="yellow")
        return
    
    import csv
    export_file = "coalesce_export.csv"
    
    with open(export_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(["Problem ID", "Problem Link", "Rating", "Tags", "Submission ID", "Submission Link", "Submission Time"])
        
        # Write data
        for problem in problems:
            tags_str = ", ".join(problem["tags"])
            submission_time = datetime.fromtimestamp(problem["submission_time"]).strftime("%Y-%m-%d %H:%M:%S")
            
            writer.writerow([
                problem["problem_id"],
                problem["problem_link"],
                problem["rating"],
                tags_str,
                problem["submission_id"],
                problem["submission_link"],
                submission_time
            ])
    
    click.secho(f"Data exported to {export_file}", fg="green")


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except Exception as e:
        click.secho(f"Error: {str(e)}", fg="red")
        sys.exit(1)


if __name__ == "__main__":
    main()
