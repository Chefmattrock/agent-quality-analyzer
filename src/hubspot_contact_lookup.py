#!/usr/bin/env python3
"""
HubSpot Contact Lookup Script

PURPOSE:
This script fetches contact information from HubSpot using platform_user_tokens and stores
the data in a local SQLite database. It's used to enrich agent author data with contact
details like email, name, and credit balances.

USAGE:
Single user lookup:
    python hubspot_contact_lookup.py -u <user_token>

Batch processing from CSV:
    python hubspot_contact_lookup.py -f <csv_file_with_user_tokens>

Optional flags:
    -o <output.csv>     Save successful lookups to CSV file
    --error_log <file>  Specify error log file (default: hubspot_errors.log)
    --skip-existing     Skip users that already exist in database (default: False)
    --force-refresh     Force refresh all users even if they exist (default: False)

REQUIREMENTS:
- HUB_API_KEY and HUB_ID in .env file
- CSV files must have a 'user_token' column for batch processing
- Creates/updates 'users' table in data/agents.db

WHAT IT FETCHES:
- email
- firstname  
- lastname
- agentai_platform_credits_balance

This script is typically called by refresh_data.py as part of the data refresh process.
"""

import os
import sys
import requests
from dotenv import load_dotenv
import argparse
import sqlite3
import pandas as pd
import time

# Load environment variables
load_dotenv()
HUB_API_KEY = os.getenv('HUB_API_KEY')
HUB_ID = os.getenv('HUB_ID')

DB_PATH = 'data/agents.db'

def initialize_users_table(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_token TEXT PRIMARY KEY,
            email TEXT,
            firstname TEXT,
            lastname TEXT,
            agentai_platform_credits_balance TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def user_exists_in_db(user_token, db_path=DB_PATH):
    """Check if user already exists in the database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE user_token = ?", (user_token,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def get_existing_users_batch(user_tokens, db_path=DB_PATH):
    """Get all existing users from a list of user tokens in one query."""
    if not user_tokens:
        return set()
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create placeholders for IN clause
    placeholders = ','.join('?' * len(user_tokens))
    query = f"SELECT user_token FROM users WHERE user_token IN ({placeholders})"
    
    c.execute(query, user_tokens)
    existing = {row[0] for row in c.fetchall()}
    conn.close()
    return existing

def upsert_user(user_token, email, firstname, lastname, credits_balance, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        INSERT INTO users (user_token, email, firstname, lastname, agentai_platform_credits_balance, last_updated)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_token) DO UPDATE SET
            email=excluded.email,
            firstname=excluded.firstname,
            lastname=excluded.lastname,
            agentai_platform_credits_balance=excluded.agentai_platform_credits_balance,
            last_updated=CURRENT_TIMESTAMP
    ''', (user_token, email, firstname, lastname, credits_balance))
    conn.commit()
    conn.close()

def log_error(error_log_path, message):
    with open(error_log_path, 'a') as f:
        f.write(message + '\n')

def fetch_and_store_user(user_token, error_log_path=None, skip_existing=False):
    # Check if user exists and skip if requested
    if skip_existing and user_exists_in_db(user_token):
        print(f"Skipping existing user: {user_token}")
        return "SKIPPED"
    
    url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
    headers = {
        "Authorization": f"Bearer {HUB_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "platform_user_token",
                        "operator": "EQ",
                        "value": user_token
                    }
                ]
            }
        ],
        "properties": [
            "email",
            "firstname",
            "lastname",
            "agentai_platform_credits_balance"
        ],
        "limit": 1
    }
    try:
        response = requests.post(url, headers=headers, json=body)
        if response.status_code == 401:
            msg = f"[ERROR] Authentication failed for user_token {user_token}. Check your HUB_API_KEY."
            if error_log_path:
                log_error(error_log_path, msg)
            return None
        if response.status_code != 200:
            msg = f"[ERROR] Status code {response.status_code} for user_token {user_token}\n{response.text}"
            if error_log_path:
                log_error(error_log_path, msg)
            return None
        data = response.json()
        results = data.get('results', [])
        if not results:
            msg = f"[ERROR] No contact found with platform_user_token: {user_token}"
            if error_log_path:
                log_error(error_log_path, msg)
            return None
        contact = results[0]
        props = contact.get('properties', {})
        upsert_user(
            user_token,
            props.get('email'),
            props.get('firstname'),
            props.get('lastname'),
            props.get('agentai_platform_credits_balance')
        )
        print(f"Upserted user: {user_token} ({props.get('email')})")
        # Return the data for CSV output
        return {
            'user_token': user_token,
            'email': props.get('email'),
            'firstname': props.get('firstname'),
            'lastname': props.get('lastname'),
            'agentai_platform_credits_balance': props.get('agentai_platform_credits_balance')
        }
    except Exception as e:
        msg = f"[ERROR] Exception for user_token {user_token}: {e}"
        if error_log_path:
            log_error(error_log_path, msg)
        return None

if not HUB_API_KEY:
    print("Error: HUB_API_KEY not set in .env file.")
    sys.exit(1)

parser = argparse.ArgumentParser(description="Lookup HubSpot contact(s) by platform_user_token.")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-u', '--user_token', help='The platform_user_token to look up')
group.add_argument('-f', '--file', help='CSV file with a column named user_token')
parser.add_argument('-o', '--output', help='Output CSV file for successfully pulled user data')
parser.add_argument('--error_log', default='hubspot_errors.log', help='File to log errors (default: hubspot_errors.log)')
parser.add_argument('--skip-existing', action='store_true', help='Skip users that already exist in database')
parser.add_argument('--force-refresh', action='store_true', help='Force refresh all users even if they exist')
parser.add_argument('--progress-interval', type=int, default=100, help='Show progress every N records (default: 100)')
args = parser.parse_args()

# Ensure users table exists
initialize_users_table()

output_rows = []

if args.user_token:
    result = fetch_and_store_user(args.user_token, error_log_path=args.error_log, skip_existing=args.skip_existing)
    if args.output and result and result != "SKIPPED":
        pd.DataFrame([result]).to_csv(args.output, index=False)
elif args.file:
    df = pd.read_csv(args.file)
    if 'user_token' not in df.columns:
        print("CSV file must have a column named 'user_token'.")
        sys.exit(1)
    
    user_tokens = df['user_token'].tolist()
    total = len(user_tokens)
    
    # Optimize by checking existing users in batch
    if args.skip_existing and not args.force_refresh:
        print(f"🔍 Checking which users already exist in database...")
        existing_users = get_existing_users_batch(user_tokens)
        tokens_to_process = [token for token in user_tokens if token not in existing_users]
        skipped_count = len(existing_users)
        print(f"📊 Found {skipped_count} existing users, will process {len(tokens_to_process)} new users")
    else:
        tokens_to_process = user_tokens
        skipped_count = 0
    
    success = 0
    fail = 0
    
    # Process remaining tokens
    for idx, user_token in enumerate(tokens_to_process):
        # Show progress every N records
        if (idx + 1) % args.progress_interval == 0 or idx == 0:
            print(f"🔄 Processing {idx+1}/{len(tokens_to_process)}: {user_token}")
        
        result = fetch_and_store_user(user_token, error_log_path=args.error_log, skip_existing=False)  # Already filtered
        if result and result != "SKIPPED":
            success += 1
            output_rows.append(result)
        else:
            fail += 1
            
        # Small delay to avoid overwhelming HubSpot API
        time.sleep(0.1)
    
    print(f"\n📊 Batch complete!")
    print(f"   Skipped existing: {skipped_count}")
    print(f"   Successfully processed: {success}")
    print(f"   Failed: {fail}")
    print(f"   Total in file: {total}")
    print(f"Errors logged to {args.error_log}")
    
    if args.output and output_rows:
        pd.DataFrame(output_rows).to_csv(args.output, index=False)
        print(f"Output written to {args.output}") 