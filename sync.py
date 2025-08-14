#!/usr/bin/env python3
"""
Sync script to compare CSV data with Airtable records.
Reads CSV, fetches from Airtable, compares by email and updated_at.
Outputs operation report to stdout.
"""

import argparse
import csv
import os
import sys
from datetime import datetime
import requests
from typing import Dict, List, Tuple

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Load from script directory first, then parent directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(script_dir, '.env')
    if not os.path.exists(dotenv_path):
        dotenv_path = os.path.join(script_dir, '..', '.env')
    load_dotenv(dotenv_path)
except ImportError:
    pass


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Sync CSV data with Airtable records'
    )
    parser.add_argument(
        '--csv',
        required=True,
        help='Path to CSV file'
    )
    parser.add_argument(
        '--base',
        required=True,
        help='Airtable Base ID'
    )
    parser.add_argument(
        '--table',
        required=True,
        help='Airtable Table Name'
    )
    parser.add_argument(
        '--api-key',
        default=os.environ.get('AIRTABLE_API_KEY'),
        help='Airtable API Key (defaults to AIRTABLE_API_KEY env var)'
    )
    return parser.parse_args()


def read_csv(file_path: str) -> Dict[str, Dict]:
    """Read CSV file and return dictionary keyed by email."""
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


def fetch_airtable_records(base_id: str, table_name: str, api_key: str) -> Dict[str, Dict]:
    """Fetch all records from Airtable via REST API v0."""
    url = f'https://api.airtable.com/v0/{base_id}/{table_name}'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    all_records = {}
    offset = None
    
    while True:
        params = {}
        if offset:
            params['offset'] = offset
            
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching from Airtable: {response.status_code}", file=sys.stderr)
            print(f"Response: {response.text}", file=sys.stderr)
            sys.exit(1)
            
        data = response.json()
        
        for record in data.get('records', []):
            fields = record.get('fields', {})
            email = fields.get('email')
            if email:
                all_records[email] = {
                    'first_name': fields.get('first_name', ''),
                    'last_name': fields.get('last_name', ''),
                    'updated_at': fields.get('updated_at', '')
                }
        
        offset = data.get('offset')
        if not offset:
            break
            
    return all_records


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO-8601 timestamp string to datetime object."""
    try:
        # Handle both with and without microseconds
        if '.' in timestamp_str:
            # Remove everything after the dot except the Z
            base, rest = timestamp_str.rsplit('.', 1)
            if rest.endswith('Z'):
                timestamp_str = base + 'Z'
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except:
        # Fallback for other formats
        return datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')


def compare_records(csv_records: Dict, airtable_records: Dict) -> List[Tuple[str, str, str]]:
    """
    Compare CSV and Airtable records.
    Returns list of (operation, target, email) tuples.
    """
    results = []
    
    # Process all unique emails
    all_emails = set(csv_records.keys()) | set(airtable_records.keys())
    
    for email in sorted(all_emails):
        in_csv = email in csv_records
        in_airtable = email in airtable_records
        
        if in_csv and not in_airtable:
            # Email appears in CSV only
            results.append(('CREATE', 'AIRTABLE', email))
        elif in_airtable and not in_csv:
            # Email appears in Airtable only
            results.append(('CREATE', 'CSV', email))
        elif in_csv and in_airtable:
            # Email appears in both - compare timestamps
            csv_timestamp = parse_timestamp(csv_records[email]['updated_at'])
            airtable_timestamp = parse_timestamp(airtable_records[email]['updated_at'])
            
            if csv_timestamp == airtable_timestamp:
                # Timestamps are equal
                results.append(('NONE', '', email))
            elif csv_timestamp > airtable_timestamp:
                # CSV is newer, Airtable needs update
                results.append(('UPDATE', 'AIRTABLE', email))
            else:
                # Airtable is newer, CSV needs update
                results.append(('UPDATE', 'CSV', email))
    
    return results


def main():
    """Main execution function."""
    args = parse_args()
    
    if not args.api_key:
        print("Error: Airtable API key not provided. Use --api-key or set AIRTABLE_API_KEY environment variable.", file=sys.stderr)
        sys.exit(1)
    
    # Read CSV data
    try:
        csv_records = read_csv(args.csv)
    except FileNotFoundError:
        print(f"Error: CSV file not found: {args.csv}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Fetch Airtable data
    try:
        airtable_records = fetch_airtable_records(args.base, args.table, args.api_key)
    except Exception as e:
        print(f"Error fetching Airtable records: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Compare records
    results = compare_records(csv_records, airtable_records)
    
    # Output results as CSV to stdout
    print("operation,target,email")
    for operation, target, email in results:
        print(f"{operation},{target},{email}")


if __name__ == '__main__':
    main()