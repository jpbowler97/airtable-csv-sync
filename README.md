# Airtable CSV Sync

A Python script that compares CSV data with Airtable records to identify synchronization operations needed.

## Overview

This script reads a CSV file and compares it with records from an Airtable table based on email addresses and timestamps. It outputs a report showing what operations would be needed to synchronize the two data sources.

## Requirements

- Python 3.6+
- `requests` library

## Installation

```bash
pip install requests
```

## Setup

1. Create an Airtable account and workspace
2. Create a table with columns: `email`, `first_name`, `last_name`, `updated_at`
3. Get your Airtable API key from [Airtable Account](https://airtable.com/account)
4. Get your Base ID from the Airtable API documentation for your base
5. Note your table name

## Usage

```bash
# Set your Airtable API key as an environment variable
export AIRTABLE_API_KEY=keyXXXXXXXX

# Run the sync script
python sync.py \
  --base appYYYYYYYY \
  --table "People" \
  --csv people.csv
```

### Command Line Arguments

- `--csv`: Path to the CSV file containing local data
- `--base`: Airtable Base ID (starts with 'app')
- `--table`: Name of the Airtable table
- `--api-key`: Airtable API key (optional if set as environment variable)

## Output Format

The script outputs a CSV report to stdout with three columns:

```
operation,target,email
```

### Operations

- `CREATE`: Record exists in one system but not the other
- `UPDATE`: Record exists in both systems but timestamps differ
- `NONE`: Record exists in both systems with identical timestamps

### Targets

- `AIRTABLE`: Operation should be performed on Airtable
- `CSV`: Operation should be performed on the CSV
- (blank): No target for NONE operations

## Example Output

```csv
operation,target,email
CREATE,AIRTABLE,charlie@example.com
CREATE,CSV,dora@example.com
UPDATE,AIRTABLE,ana@example.com
NONE,,bob@example.com
```

## How It Works

1. **Read CSV**: Loads all records from the specified CSV file
2. **Fetch Airtable**: Retrieves all records from the Airtable table via REST API
3. **Compare**: For each unique email address:
   - If only in CSV → `CREATE,AIRTABLE`
   - If only in Airtable → `CREATE,CSV`
   - If in both with different timestamps → `UPDATE` on the older side
   - If in both with same timestamp → `NONE`
4. **Output**: Prints the comparison results as CSV to stdout

## Notes

- This is a read-only integration - no data is written back to Airtable
- All timestamps are treated as UTC
- The email field is used as the unique identifier for matching records
- The script uses Airtable's REST API v0