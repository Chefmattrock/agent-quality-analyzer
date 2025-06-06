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
            agentai_platform_credits_balance TEXT
        )
    ''')
    conn.commit()
    conn.close()

def upsert_user(user_token, email, firstname, lastname, credits_balance, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        INSERT INTO users (user_token, email, firstname, lastname, agentai_platform_credits_balance)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_token) DO UPDATE SET
            email=excluded.email,
            firstname=excluded.firstname,
            lastname=excluded.lastname,
            agentai_platform_credits_balance=excluded.agentai_platform_credits_balance
    ''', (user_token, email, firstname, lastname, credits_balance))
    conn.commit()
    conn.close()

def log_error(error_log_path, message):
    with open(error_log_path, 'a') as f:
        f.write(message + '\n')

def fetch_and_store_user(user_token, error_log_path=None):
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
args = parser.parse_args()

# Ensure users table exists
initialize_users_table()

output_rows = []

if args.user_token:
    result = fetch_and_store_user(args.user_token, error_log_path=args.error_log)
    if args.output and result:
        pd.DataFrame([result]).to_csv(args.output, index=False)
elif args.file:
    df = pd.read_csv(args.file)
    if 'user_token' not in df.columns:
        print("CSV file must have a column named 'user_token'.")
        sys.exit(1)
    total = len(df)
    success = 0
    fail = 0
    for idx, user_token in enumerate(df['user_token']):
        print(f"Processing {idx+1}/{total}: {user_token}")
        result = fetch_and_store_user(user_token, error_log_path=args.error_log)
        if result:
            success += 1
            output_rows.append(result)
        else:
            fail += 1
    print(f"\nBatch complete. Success: {success}, Failed: {fail}, Total: {total}")
    print(f"Errors logged to {args.error_log}")
    if args.output and output_rows:
        pd.DataFrame(output_rows).to_csv(args.output, index=False)
        print(f"Output written to {args.output}") 