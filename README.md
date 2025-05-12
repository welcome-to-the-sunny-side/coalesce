# Coalesce

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
#   --xaxis TEXT     X-axis for the plot (week, month, or rating). Default: month.
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
```

## Features

- Track problems solved across multiple Codeforces accounts
- Automatic backups of problem data
- Filter problems by rating, tags, time, contest ID, and more
- Get random problem recommendations
- Plot solved problem counts over time or by rating
- Export data to CSV format

## Data Storage

Coalesce stores its data in the `~/.coalesce` directory:
- `problems.json`: Central database of problems
- `handles.json`: List of tracked Codeforces handles
- `backups/`: Directory containing automatic backups
