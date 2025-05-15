# Coalesce (AI-Generated Readme)

A command-line tool to track and analyze your Codeforces problem-solving data.

## Overview

Coalesce maintains a central database of problems you've solved across multiple Codeforces accounts. It supports various data analysis features, including filtering problems by rating, tags, time range, and more.

## Installation

### Using Homebrew

```bash
brew tap welcome-to-the-sunny-side/coalesce
brew install coalesce
```

### From Source

```bash
# Clone the repository
git clone https://github.com/welcome-to-the-sunny-side/coalesce.git
cd coalesce

# Install the package
pip install -e .
```

## Usage

### Managing Handles

```bash
# Add a Codeforces handle to track
coalesce add <handle>

# Remove a Codeforces handle
coalesce remove <handle>

# View all tracked handles
coalesce whoami
```

### Data Management

```bash
# Update the central database with the latest problems
coalesce pull

# Export problem data to CSV
coalesce export

# Configure auto-refresh settings
coalesce config [OPTIONS]

# Options:
#   --auto-refresh [on|off]  Enable or disable auto-refresh
#   --period FLOAT           Auto-refresh period in days (0 for manual only)
#   --show                   Show current configuration
```

### Problem Analysis

```bash
# List problems matching criteria
coalesce list [OPTIONS]

# Options:
#   --rating TEXT    Rating range (format: x-y, default: 0-3500)
#   --tag_and TEXT   Problem must have ALL these tags (comma-separated)
#   --tag_or TEXT    Problem must have AT LEAST ONE of these tags (comma-separated)
#   --time TEXT      Time range (format: DD/MM/YYYY-DD/MM/YYYY or keywords)
#   --cid TEXT       Contest ID range (format: x-y)
#   --pid TEXT       Problem ID
#   --verbose        Show all columns (rating, tags, submission info). Default: false.

# List ALL problems from Codeforces problemset matching criteria
coalesce pset [OPTIONS]

# Options:
#   --rating TEXT    Rating range (format: x-y, default: 0-3500)
#   --tag_and TEXT   Problem must have ALL these tags (comma-separated)
#   --tag_or TEXT    Problem must have AT LEAST ONE of these tags (comma-separated)
#   --cid TEXT       Contest ID range (format: x-y)
#   --pid TEXT       Problem ID (e.g. 123A)
#   --solved TEXT    Filter by solved status ('true', 'false', or omit for all)
#   --verbose        Show all columns (name, rating, tags, contest_id, index, link, solved). Default: false.

# Get a random problem matching criteria
coalesce gimme [OPTIONS]

# Options:
#   --spoil          Show problem rating and tags
#   --rating TEXT    Rating range (format: x-y, default: 0-3500)
#   --tag_and TEXT   Problem must have ALL these tags (comma-separated)
#   --tag_or TEXT    Problem must have AT LEAST ONE of these tags (comma-separated)
#   --cid TEXT       Contest ID range (format: x-y)
#   --solved         Include problems that are already solved

# Plot solved problems count from local data based on criteria
coalesce plot [OPTIONS]

# Options:
#   --rating TEXT    Rating range (format: x-y, default: 0-3500)
#   --tag_and TEXT   Problem must have ALL these tags (comma-separated)
#   --tag_or TEXT    Problem must have AT LEAST ONE of these tags (comma-separated)
#   --time TEXT      Time range (format: DD/MM/YYYY-DD/MM/YYYY or keywords)
#   --cid TEXT       Contest ID range (format: x-y)
#   --xaxis TEXT     X-axis for the plot (week, month, year, or rating). Default: month.
```

### Examples

```bash
# Find a random problem with rating between 1200 and 1500
coalesce gimme --rating 1200-1500

# List only IDs and links for problems with the "dp" tag solved this week
coalesce list --tag_and dp --time "this week"

# List all details for problems with the "dp" tag solved this week
coalesce list --tag_and dp --time "this week" --verbose

# Find an unsolved problem with either "graphs" or "trees" tag
coalesce gimme --tag_or graphs,trees

# Plot monthly solves from local data for problems rated 1600-1800
coalesce plot --rating 1600-1800 --xaxis month

# Plot yearly solves from local data
coalesce plot --xaxis year
```

## Auto-Refresh System

**NEW:** Coalesce now features a smart auto-refresh system that minimizes API calls to Codeforces.

- **Default behavior**: Automatically refreshes data once per day when you run any command
- **Customizable**: Set your preferred refresh period or disable auto-refresh entirely
- **Manual option**: Set refresh period to 0 to only update when explicitly running `pull`
- **Persistent**: Your settings are saved between sessions

```bash
# View current configuration
coalesce config --show

# Disable auto-refresh
coalesce config --auto-refresh off

# Enable auto-refresh with default period (1 day)
coalesce config --auto-refresh on

# Set a custom refresh period (e.g., 3.5 days)
coalesce config --period 3.5

# Set to manual refresh only
coalesce config --period 0
```

## Features

- Track problems solved across multiple Codeforces accounts
- Automatic backups of problem data
- **NEW: Smart caching of all Codeforces problems with configurable auto-refresh**
- **NEW: Configuration management with customizable refresh periods**
- **NEW: Automatic problem database updates when handles are added/removed**
- Filter problems by rating, tags, time, contest ID, and more
- Get random problem recommendations
- Plot solved problem counts over time (by week, month, or year) or by rating
- Plots use green color for better visibility
- Export data to CSV format

## Data Storage

Coalesce stores its data in the `~/.coalesce` directory:
- `problems.json`: Central database of solved problems
- `all_problems.json`: **NEW: Cache of all Codeforces problems**
- `config.json`: **NEW: Configuration file including handles and settings**
- `backups/`: Directory containing automatic backups
