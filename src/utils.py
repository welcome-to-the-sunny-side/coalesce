from datetime import datetime, timedelta
from dateutil.parser import parse as dateutil_parse
from dateutil.relativedelta import relativedelta
from rich.console import Console
from rich.table import Table


def parse_date_range_input(time_param_str):
    """
    Parses a time parameter string into a start and end datetime object (inclusive).
    Supports:
    - "dd/mm/yyyy-dd/mm/yyyy"
    - "today", "yesterday"
    - "this week", "this month", "this year"
    - "last week", "last month", "last year"
    Returns (start_date, end_date) or (None, None) if parsing fails.
    Timestamps are set to start of the start day and end of the end day.
    """
    if not time_param_str:
        return None, None

    now = datetime.now()
    start_date = None
    end_date = None

    time_param_lower = time_param_str.lower()

    try:
        if '-' in time_param_lower and '/' in time_param_lower:
            start_str, end_str = time_param_lower.split('-')
            # Assuming dd/mm/yyyy
            start_date = datetime.strptime(start_str.strip(), "%d/%m/%Y")
            end_date = datetime.strptime(end_str.strip(), "%d/%m/%Y")
        elif time_param_lower == "today":
            start_date = now
            end_date = now
        elif time_param_lower == "yesterday":
            start_date = now - timedelta(days=1)
            end_date = start_date
        elif time_param_lower == "this week":
            start_date = now - timedelta(days=now.weekday())
            end_date = start_date + timedelta(days=6)
        elif time_param_lower == "last week":
            end_of_last_week = now - timedelta(days=now.weekday() + 1)
            start_date = end_of_last_week - timedelta(days=6)
            end_date = end_of_last_week
        elif time_param_lower == "this month":
            start_date = now.replace(day=1)
            # Next month's first day, then subtract one day
            next_month = (now.replace(day=28) + timedelta(days=4)).replace(day=1) # handles month end safely
            end_date = next_month - timedelta(days=1)
        elif time_param_lower == "last month":
            first_day_current_month = now.replace(day=1)
            end_date = first_day_current_month - timedelta(days=1)
            start_date = end_date.replace(day=1)
        elif time_param_lower == "this year":
            start_date = now.replace(month=1, day=1)
            end_date = now.replace(month=12, day=31)
        elif time_param_lower == "last year":
            last_year_num = now.year - 1
            start_date = now.replace(year=last_year_num, month=1, day=1)
            end_date = now.replace(year=last_year_num, month=12, day=31)
        else:
            # Try to parse as a single date if no keyword matched
            # This is not explicitly in spec but can be a fallback
            parsed_single_date = dateutil_parse(time_param_str)
            start_date = parsed_single_date
            end_date = parsed_single_date

        if start_date and end_date:
            # Set time to beginning of start_date and end of end_date for full day coverage
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            return start_date, end_date

    except ValueError as e:
        # print(f"Error parsing date: {e}") # For debugging
        return None, None
    
    return None, None

def render_problems_table(problems_list):
    """Renders a list of problem dictionaries as a table in the terminal."""
    if not problems_list:
        print("No problems to display.")
        return

    table = Table(title="Solved Problems")
    console = Console()

    # Define columns based on the keys in the problem dictionary
    # Using a predefined set for consistency and order from the spec
    headers = ["Problem Identifier", "Problem Link", "Rating", "Tags", "Submission ID", "Link to Submission", "Submission Time"]
    for header in headers:
        table.add_column(header, overflow="fold")

    for problem in problems_list:
        row_data = []
        for header in headers:
            value = problem.get(header)
            if header == "Tags" and isinstance(value, list):
                row_data.append(", ".join(value) if value else "-")
            elif header == "Submission Time" and isinstance(value, (int, float)):
                # Convert Unix timestamp to human-readable format
                try:
                    dt_object = datetime.fromtimestamp(value)
                    row_data.append(dt_object.strftime("%Y-%m-%d %H:%M:%S"))
                except (TypeError, ValueError):
                     row_data.append(str(value) if value is not None else "-") # Fallback if conversion fails
            elif value is None:
                row_data.append("-") # Display '-' for None values
            else:
                row_data.append(str(value))
        table.add_row(*row_data)
    
    console.print(table)

