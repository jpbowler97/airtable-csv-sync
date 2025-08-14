# Airtable CSV Sync Tool

A Python script that compares CSV data with Airtable records to identify synchronization operations needed between the two data sources.

## Overview

This tool reads a CSV file and compares it with records from an Airtable table based on:
- **Email addresses** as unique identifiers
- **Timestamps** to determine which version is newer

It outputs a report showing what operations would be needed to synchronize the data.

## Installation

```bash
# Clone the repository
git clone https://github.com/jpbowler97/airtable-csv-sync.git
cd airtable-csv-sync

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Airtable credentials
```

## Usage

```bash
python sync.py --base BASE_ID --table "TABLE_NAME" --csv CSV_FILE
```

### Example

```bash
python sync.py --base appxguEEEuSQOl3Ie --table "People" --csv people.csv
```

## Output Format

The script outputs a CSV report with three columns:

| Column | Description |
|--------|-------------|
| `operation` | The sync operation needed: `CREATE`, `UPDATE`, or `NONE` |
| `target` | Where the operation should be applied: `AIRTABLE`, `CSV`, or empty |
| `email` | The email address of the record |

### Operations Explained

- **`CREATE,AIRTABLE`** - Record exists only in CSV, needs to be created in Airtable
- **`CREATE,CSV`** - Record exists only in Airtable, needs to be added to CSV
- **`UPDATE,AIRTABLE`** - Record in CSV is newer, Airtable needs updating
- **`UPDATE,CSV`** - Record in Airtable is newer, CSV needs updating
- **`NONE`** - Records are synchronized (same timestamp)

## Sample Data

The repository includes `people.csv` with test data to demonstrate the tool's functionality.

## Configuration

### Environment Variables

Create a `.env` file with your Airtable credentials:

```
AIRTABLE_API_KEY=patXXXXXXXXXX
```

### Command Line Arguments

- `--base` - Your Airtable Base ID (starts with 'app')
- `--table` - Name of your Airtable table
- `--csv` - Path to your CSV file
- `--api-key` - Optional, overrides environment variable

## Requirements

- Python 3.6+
- `requests` library for API calls
- `python-dotenv` for environment variables

## Note

This is a **read-only** tool - it identifies what needs to be synchronized but does not modify any data in either the CSV or Airtable.