#!/usr/bin/env python3
"""
Airtable CSV Sync Tool
Compares CSV data with Airtable records to identify sync operations.
"""

import argparse
import csv
import os
import sys
from datetime import datetime
import requests
from typing import Dict, List, Tuple

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ============================================================================
# CONFIGURATION
# ============================================================================

def parse_arguments():
    """Parse command line arguments for CSV path, Airtable base, and table."""
    parser = argparse.ArgumentParser(
        description='Compare CSV data with Airtable records'
    )
    parser.add_argument('--csv', required=True, help='Path to CSV file')
    parser.add_argument('--base', required=True, help='Airtable Base ID')
    parser.add_argument('--table', required=True, help='Airtable Table Name')
    parser.add_argument('--api-key', 
                       default=os.environ.get('AIRTABLE_API_KEY'),
                       help='Airtable API Key (or set AIRTABLE_API_KEY env var)')
    
    args = parser.parse_args()
    
    # Validate API key is present
    if not args.api_key:
        exit_with_error("Airtable API key not provided. "
                       "Use --api-key or set AIRTABLE_API_KEY environment variable.")
    
    return args


# ============================================================================
# DATA LOADING
# ============================================================================

def load_csv_data(file_path: str) -> Dict[str, Dict]:
    """Load CSV file and return records as dictionary keyed by email."""
    try:
        records = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row['email']
                records[email] = {
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'updated_at': row['updated_at']
                }
        return records
    except FileNotFoundError:
        exit_with_error(f"CSV file not found: {file_path}")
    except Exception as e:
        exit_with_error(f"Error reading CSV file: {e}")


def load_airtable_data(base_id: str, table_name: str, api_key: str) -> Dict[str, Dict]:
    """Fetch all records from Airtable table via REST API."""
    url = f'https://api.airtable.com/v0/{base_id}/{table_name}'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        all_records = {}
        offset = None
        
        # Paginate through all records (Airtable returns max 100 at a time)
        while True:
            params = {'offset': offset} if offset else {}
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                exit_with_error(f"Airtable API error {response.status_code}: {response.text}")
            
            data = response.json()
            
            # Extract records from Airtable response
            for record in data.get('records', []):
                fields = record.get('fields', {})
                email = fields.get('email')
                if email:
                    all_records[email] = {
                        'first_name': fields.get('first_name', ''),
                        'last_name': fields.get('last_name', ''),
                        'updated_at': fields.get('updated_at', '')
                    }
            
            # Check if there are more pages
            offset = data.get('offset')
            if not offset:
                break
                
        return all_records
        
    except requests.exceptions.RequestException as e:
        exit_with_error(f"Network error connecting to Airtable: {e}")
    except Exception as e:
        exit_with_error(f"Error fetching Airtable records: {e}")


# ============================================================================
# COMPARISON LOGIC
# ============================================================================

def parse_timestamp(timestamp_str: str) -> datetime:
    """Convert ISO-8601 timestamp string to datetime object."""
    # Remove microseconds if present (everything between . and Z)
    if '.' in timestamp_str and timestamp_str.endswith('Z'):
        timestamp_str = timestamp_str.split('.')[0] + 'Z'
    
    # Convert to datetime
    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))


def compare_datasets(csv_data: Dict, airtable_data: Dict) -> List[Tuple[str, str, str]]:
    """
    Compare CSV and Airtable datasets to determine sync operations.
    
    Returns list of (operation, target, email) tuples where:
    - operation: CREATE, UPDATE, or NONE
    - target: CSV, AIRTABLE, or empty
    - email: the email address
    """
    results = []
    
    # Get all unique emails from both datasets
    all_emails = set(csv_data.keys()) | set(airtable_data.keys())
    
    # Check each email to determine required operation
    for email in sorted(all_emails):
        in_csv = email in csv_data
        in_airtable = email in airtable_data
        
        if in_csv and not in_airtable:
            # Record exists only in CSV → Create in Airtable
            results.append(('CREATE', 'AIRTABLE', email))
            
        elif not in_csv and in_airtable:
            # Record exists only in Airtable → Create in CSV
            results.append(('CREATE', 'CSV', email))
            
        else:
            # Record exists in both → Compare timestamps
            csv_time = parse_timestamp(csv_data[email]['updated_at'])
            airtable_time = parse_timestamp(airtable_data[email]['updated_at'])
            
            if csv_time == airtable_time:
                # Same timestamp → No action needed
                results.append(('NONE', '', email))
            elif csv_time > airtable_time:
                # CSV is newer → Update Airtable
                results.append(('UPDATE', 'AIRTABLE', email))
            else:
                # Airtable is newer → Update CSV
                results.append(('UPDATE', 'CSV', email))
    
    return results


# ============================================================================
# OUTPUT & UTILITIES
# ============================================================================

def print_results(results: List[Tuple[str, str, str]]):
    """Print comparison results as CSV to stdout."""
    print("operation,target,email")
    for operation, target, email in results:
        print(f"{operation},{target},{email}")


def exit_with_error(message: str):
    """Print error message to stderr and exit."""
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution flow."""
    # Step 1: Parse command line arguments
    args = parse_arguments()
    
    # Step 2: Load data from CSV file
    csv_data = load_csv_data(args.csv)
    
    # Step 3: Fetch data from Airtable
    airtable_data = load_airtable_data(args.base, args.table, args.api_key)
    
    # Step 4: Compare datasets
    results = compare_datasets(csv_data, airtable_data)
    
    # Step 5: Output results
    print_results(results)


if __name__ == '__main__':
    main()