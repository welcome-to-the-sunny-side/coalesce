"""
Command-line interface for coalesce.
"""

import click
import json
import random
import sys
import time
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich import box
import plotext as plt
from collections import defaultdict
import math

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
    """Refresh both data files with the latest problems."""
    click.echo("Refreshing problem data from Codeforces...")
    
    data_manager = DataManager()
    
    # Update all problems file first
    click.echo("Updating exhaustive problem cache...")
    all_problems, cache_message = data_manager.get_all_problems(force_refresh=True)
    click.secho(cache_message, fg="green")
    
    # Then update solved problems
    click.echo("Updating your solved problems data...")
    success, message = data_manager.update_problems_data()
    
    if success:
        click.secho(message, fg="green")
    else:
        click.secho(f"Error: {message}", fg="red")


@cli.command()
@click.argument("handle")
def add(handle):
    """Add a Codeforces handle to track."""
    data_manager = DataManager()
    data_manager.lazy_refresh()  # Run lazy refresh first
    success, message = data_manager.add_handle(handle)
    
    if success:
        click.secho(message, fg="green")
        click.echo("Updating problems data with the new handle...")
        
        # Automatically pull problem data
        pull_success, pull_message = data_manager.update_problems_data()
        
        if pull_success:
            click.secho(pull_message, fg="green")
        else:
            click.secho(f"Warning: {pull_message}", fg="yellow")
    else:
        click.secho(f"Error: {message}", fg="red")


@cli.command()
@click.argument("handle")
def remove(handle):
    """Remove a Codeforces handle from tracking."""
    data_manager = DataManager()
    data_manager.lazy_refresh()  # Run lazy refresh first
    success, message = data_manager.remove_handle(handle)
    
    if success:
        click.secho(message, fg="green")
        click.echo("Updating problems data after handle removal...")
        
        # Automatically pull problem data
        pull_success, pull_message = data_manager.update_problems_data()
        
        if pull_success:
            click.secho(pull_message, fg="green")
        else:
            click.secho(f"Warning: {pull_message}", fg="yellow")
    else:
        click.secho(f"Error: {message}", fg="red")


@cli.command()
def whoami():
    """Show the list of tracked Codeforces handles."""
    data_manager = DataManager()
    data_manager.lazy_refresh()  # Run lazy refresh first
    handles = data_manager.get_handles()
    
    if not handles:
        click.echo("No handles are being tracked.")
        click.echo("Add a handle with 'coalesce add <handle>'")
        return
    
    click.echo("Tracked handles:")
    for handle in handles:
        click.echo(f"  {handle}")


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
    data_manager.lazy_refresh()  # Run lazy refresh first
    
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
    
    # Get problems (either solved problems or all problems minus solved ones)
    if solved:
        problems = data_manager.get_problems(filters)
    else:
        # For unsolved problems, use the cached all problems data and filter out solved ones
        all_problems, _ = data_manager.get_all_problems()
        
        if not all_problems:
            click.secho("Failed to fetch or load Codeforces problems", fg="red")
            return
        
        # Get list of solved problem IDs
        solved_problems = data_manager.get_problems()
        solved_ids = {p["problem_id"] for p in solved_problems}
        
        # Filter unsolved problems that match our criteria
        unsolved_problems = []
        for problem in all_problems:
            # Skip if already solved
            if problem["problem_id"] in solved_ids:
                continue
                
            # Only include problems that match our filters
            if data_manager._matches_filters(problem, filters):
                unsolved_problems.append(problem)
        
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
@click.option("--rating", help="Rating range (x-y, default 0‑3500)")
@click.option("--tag_and", help="Problem must have ALL these tags")
@click.option("--tag_or", help="Problem must have AT LEAST ONE of these tags")
@click.option("--time", help="Time range (DD/MM/YYYY‑DD/MM/YYYY or keywords)")
@click.option("--cid", help="Contest ID range (x-y)")
@click.option("--pid", help="Specific problem ID")
@click.option("--verbose", is_flag=True, help="Show more details")
def list_cmd(rating, tag_and, tag_or, time, cid, pid, verbose):
    """List problems matching the given criteria."""
    data_manager = DataManager()
    data_manager.lazy_refresh()  # Run lazy refresh first
    
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
        filters["cid_range"] = parse_cid_range(cid)
    
    if pid:
        filters["problem_id"] = pid
    
    # Get problems
    problems = data_manager.get_problems(filters=filters)
    
    if not problems:
        click.secho("No problems found matching the criteria", fg="yellow")
        return
    
    # Prepare the data for display based on verbosity
    table_data = []
    if verbose:
        headers = ["Problem ID", "Problem Link", "Rating", "Tags", "Submission ID", "Submission Link", "Submission Time"]
        for problem in problems:
            submission_time = datetime.fromtimestamp(problem["submission_time"]).strftime("%Y-%m-%d %H:%M:%S")
            tags = ", ".join(problem["tags"])
            
            problem_link = problem["problem_link"]
            submission_link = problem["submission_link"]
            
            table_data.append([
                problem["problem_id"],
                problem_link,
                problem["rating"],
                tags,
                problem["submission_id"],
                submission_link,
                submission_time
            ])
    else: # Not verbose - only Problem ID and Link
        headers = ["Problem ID", "Problem Link"]
        for problem in problems:
            table_data.append([
                problem["problem_id"],
                problem["problem_link"] 
            ])

    # Display the table
    console = Console()
    # Get the current terminal width
    term_width = console.width
    
    # Let Rich auto-adjust to terminal width
    table = Table(
        show_header=True, 
        header_style="", 
        style="green",
        border_style="green", 
        show_lines=True,
        box=box.ROUNDED
    )
    
    # Add columns with appropriate handling for different content types
    for i, header in enumerate(headers):
        # Special handling for different column types
        if header == "Problem Link" or header == "Submission Link":
            table.add_column(header, no_wrap=True)
        elif header == "Tags":
            table.add_column(header, overflow="ellipsis")
        elif header == "Problem ID":
            table.add_column(header, justify="center")
        elif header == "Rating":
            table.add_column(header, justify="center")
        elif header == "Submission ID":
            table.add_column(header, justify="center")
        else:
            table.add_column(header)
    
    # Add rows
    for row in table_data:
        table.add_row(*[str(cell) for cell in row])
    
    console.print(table)
    click.echo(f"Total problems: {len(problems)}")


@cli.command()
def export():
    """Export the problem data to a CSV file."""
    import csv
    
    data_manager = DataManager()
    data_manager.lazy_refresh()  # Run lazy refresh first
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


@cli.command()
@click.option("--rating",   help="Rating range (x-y, default 0‑3500)")
@click.option("--tag_and",  help="Problem must have ALL these tags")
@click.option("--tag_or",   help="Problem must have AT LEAST ONE of these tags")
@click.option("--time",     help="Time range (DD/MM/YYYY‑DD/MM/YYYY or keywords)")
@click.option("--cid",      help="Contest ID range (x-y)")
@click.option("--xaxis", default="month", type=click.Choice(["week", "month", "year", "rating"]), help="X‑axis grouping (week, month, year, or rating).")
def plot(rating, tag_and, tag_or, time, cid, xaxis):
    """Plot solved‑problem counts from local data."""
    dm = DataManager()
    dm.lazy_refresh()  # Run lazy refresh first

    click.echo("Loading problems from local data file…")
    problems = dm.get_problems()
    if not problems:
        click.secho("No problems found. Run ‘coalesce pull’ first.", fg="yellow")
        return
    click.echo(f"Loaded {len(problems)} problems from local data.")

    # build filters
    f = {"rating_range": parse_rating_range(rating)}
    if tag_and: f["tag_and"]   = parse_tags(tag_and)
    if tag_or:  f["tag_or"]    = parse_tags(tag_or)
    if time:    f["time_range"]= parse_time_parameter(time)
    if cid:     f["cid_range"] = parse_cid_range(cid)

    filtered = [p for p in problems if dm._matches_filters(p, f)]
    if not filtered:
        click.secho("No problems match those filters.", fg="yellow")
        return
    click.echo(f"Plotting {len(filtered)} problems matching criteria.")

    # aggregate
    agg = defaultdict(int)
    if xaxis in ("week", "month", "year"):
        for p in filtered:
            dt = datetime.fromtimestamp(p["submission_time"])
            if xaxis == "week":
                label = (dt - timedelta(days=dt.weekday())).strftime("%G-W%V")
            elif xaxis == "month":
                label = dt.strftime("%Y-%m")
            else:  # year
                label = dt.strftime("%Y")
            agg[label] += 1
        labels = sorted(agg)
        counts = [agg[l] for l in labels]
    else:  # rating
        step = 100
        # Generate labels for every multiple of 100 in range [800, 3500]
        rating_range = range(800, 3500 + 1, step)
        for r in rating_range:
            agg[r] = 0  # Initialize all rating bins to zero
            
        for p in filtered:
            r = p.get("rating")
            if r is not None and f["rating_range"][0] <= r <= f["rating_range"][1]:
                # Map to nearest step
                rating_bin = (r // step) * step
                # Only count if in our desired display range
                if rating_bin in agg:
                    agg[rating_bin] += 1
                    
        labels = [f"{b}-{b+step-1}" for b in sorted(agg)]
        counts = [agg[b] for b in sorted(agg)]

    if not labels:
        click.secho("Nothing to plot after aggregation.", fg="yellow")
        return

    # safe categorical plot
    x_pos = list(range(len(labels)))
    plt.clf()
    plt.theme("clear")
    # plt.bar(x_pos, counts, color="green")
    plt.plot(x_pos, counts, color="green")

    plt.xticks(x_pos, labels)
    plt.xlabel("Rating Range" if xaxis == "rating" else f"{xaxis.capitalize()} Period")
    plt.ylabel("Count")
    plt.title("Solves")
    plt.grid(True, False)
    plt.show()



@cli.command()
@click.option("--auto-refresh", type=click.Choice(["on", "off"]), help="Enable or disable auto-refresh")
@click.option("--period", type=float, help="Auto-refresh period in days (0 for manual only)")
@click.option("--show", is_flag=True, help="Show current configuration")
def config(auto_refresh, period, show):
    """Configure coalesce settings."""
    data_manager = DataManager()
    current_config = data_manager.get_config()
    
    # Show current configuration if requested or if no options provided
    if show or (auto_refresh is None and period is None):
        auto_refresh_config = current_config.get("auto_refresh", {"enabled": True, "period_days": 1})
        enabled = auto_refresh_config.get("enabled", True)
        period_days = auto_refresh_config.get("period_days", 1)
        
        click.echo("Current configuration:")
        click.echo(f"  Auto-refresh: {'Enabled' if enabled else 'Disabled'}")
        if enabled:
            if period_days > 0:
                click.echo(f"  Refresh period: {period_days} day(s)")
            else:
                click.echo("  Refresh period: Manual only")
        return
    
    # Update auto-refresh setting if provided
    if auto_refresh is not None:
        enabled = auto_refresh == "on"
    else:
        # Keep current setting if not specified
        auto_refresh_config = current_config.get("auto_refresh", {"enabled": True, "period_days": 1})
        enabled = auto_refresh_config.get("enabled", True)
    
    # Update period if provided
    if period is not None:
        period_days = period
    else:
        # Keep current setting if not specified
        auto_refresh_config = current_config.get("auto_refresh", {"enabled": True, "period_days": 1})
        period_days = auto_refresh_config.get("period_days", 1)
    
    # Apply the settings
    success, message = data_manager.set_auto_refresh(enabled, period_days)
    
    if success:
        click.secho(message, fg="green")
    else:
        click.secho(f"Error: {message}", fg="red")


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except Exception as e:
        click.secho(f"Error: {str(e)}", fg="red")
        sys.exit(1)

if __name__ == "__main__":
    main()
