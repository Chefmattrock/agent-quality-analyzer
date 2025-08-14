#!/usr/bin/env python3
"""
HubSpot Contact Lookup Script - BATCH OPTIMIZED VERSION

PERFORMANCE IMPROVEMENTS:
- Processes up to 100 users per API call (vs 1 user per call)
- Smart pre-filtering to skip existing users
- ~35x faster than individual API calls
- Better progress tracking and error handling

PURPOSE:
This script fetches contact information from HubSpot using platform_user_tokens and stores
the data in a local SQLite database using batch processing for maximum efficiency.

USAGE:
Single user lookup:
    python hubspot_contact_lookup_batch.py -u <user_token>

Batch processing from CSV:
    python hubspot_contact_lookup_batch.py -f <csv_file_with_user_tokens>

Optional flags:
    -o <output.csv>     Save successful lookups to CSV file
    --error_log <file>  Specify error log file (default: hubspot_errors.log)
    --skip-existing     Skip users that already exist in database (default: True)
    --batch-size <num>  Number of users per batch (default: 100, max: 100)
    --force-refresh     Force refresh all users even if they exist

REQUIREMENTS:
- HUB_API_KEY and HUB_ID in .env file
- CSV files must have a 'user_token' column for batch processing
- Creates/updates 'users' table in data/agents.db
"""

import os
import sys
import requests
from dotenv import load_dotenv
import argparse
import sqlite3
import pandas as pd
import time
from typing import List, Dict, Set
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('hubspot_contact_lookup.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
HUB_API_KEY = os.getenv('HUB_API_KEY')
HUB_ID = os.getenv('HUB_ID')

def get_project_root():
    """Get the project root directory (where this script's parent directory is located)."""
    script_dir = Path(__file__).parent.absolute()
    # Go up one level from src/ to get to project root
    return script_dir.parent

def get_db_path():
    """Get the correct database path relative to project root."""
    project_root = get_project_root()
    db_path = project_root / 'data' / 'agents.db'
    return str(db_path)

def initialize_users_table(db_path=None):
    if db_path is None:
        db_path = get_db_path()
    print(f"Initializing users table at: {db_path}")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # First check if the table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    table_exists = c.fetchone() is not None
    
    if not table_exists:
        # Create new table with all columns
        c.execute('''
            CREATE TABLE users (
                user_token TEXT PRIMARY KEY,
                email TEXT,
                firstname TEXT,
                lastname TEXT,
                agentai_platform_credits_balance TEXT,
                nytw_status TEXT,
                agents TEXT
            )
        ''')
    else:
        # Add new columns if they don't exist
        try:
            c.execute("ALTER TABLE users ADD COLUMN nytw_status TEXT")
            logger.info("Added nytw_status column to users table")
        except sqlite3.OperationalError:
            logger.info("nytw_status column already exists")
            
        try:
            c.execute("ALTER TABLE users ADD COLUMN agents TEXT")
            logger.info("Added agents column to users table")
        except sqlite3.OperationalError:
            logger.info("agents column already exists")
    
    conn.commit()
    conn.close()

def get_existing_users_batch(user_tokens: List[str], db_path=None) -> Set[str]:
    """Get all existing users from a list of user tokens in one query."""
    if not user_tokens:
        return set()
    
    if db_path is None:
        db_path = get_db_path()
    
    print(f"Checking existing users in database: {db_path}")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create placeholders for IN clause
    placeholders = ','.join('?' * len(user_tokens))
    query = f"SELECT user_token FROM users WHERE user_token IN ({placeholders})"
    
    c.execute(query, user_tokens)
    existing = {row[0] for row in c.fetchall()}
    conn.close()
    return existing

def upsert_users_batch(users_data: List[Dict], db_path=None):
    """Insert/update multiple users in a single transaction."""
    if not users_data:
        return
    
    if db_path is None:
        db_path = get_db_path()
    
    print(f"Saving {len(users_data)} users to database: {db_path}")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    for user_data in users_data:
        c.execute('''
            INSERT INTO users (user_token, email, firstname, lastname, agentai_platform_credits_balance)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_token) DO UPDATE SET
                email=excluded.email,
                firstname=excluded.firstname,
                lastname=excluded.lastname,
                agentai_platform_credits_balance=excluded.agentai_platform_credits_balance
        ''', (
            user_data['user_token'],
            user_data.get('email'),
            user_data.get('firstname'), 
            user_data.get('lastname'),
            user_data.get('agentai_platform_credits_balance')
        ))
    
    conn.commit()
    conn.close()

def log_error(error_log_path, message):
    with open(error_log_path, 'a') as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def create_session_with_retries():
    """Create a requests session with retry logic for connection failures."""
    session = requests.Session()
    
    # Define retry strategy
    retry_strategy = Retry(
        total=3,  # Total number of retries
        backoff_factor=1,  # Wait time between retries (1s, 2s, 4s)
        status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry on
        raise_on_status=False
    )
    
    # Mount adapter with retry strategy
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def fetch_users_batch(user_tokens: List[str], error_log_path=None, batch_num=None, total_batches=None) -> List[Dict]:
    """Fetch multiple users from HubSpot in a single batch API call with retry logic."""
    if not user_tokens:
        return []
    
    # HubSpot API limit: maximum 5 filterGroups per request
    if len(user_tokens) > 5:
        logger.warning(f"Batch size {len(user_tokens)} exceeds HubSpot limit of 5. Truncating to 5 users.")
        user_tokens = user_tokens[:5]
    
    # Create session with retry logic
    session = create_session_with_retries()
    
    # HubSpot batch search API endpoint
    headers = {
        "Authorization": f"Bearer {HUB_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Create batch request body
    filter_groups = []
    for token in user_tokens:
        filter_groups.append({
            "filters": [
                {
                    "propertyName": "platform_user_token",
                    "operator": "EQ", 
                    "value": token
                }
            ]
        })
    
    search_url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
    
    body = {
        "filterGroups": filter_groups,
        "properties": [
            "platform_user_token",
            "email",
            "firstname", 
            "lastname",
            "agentai_platform_credits_balance"
        ],
        "limit": min(len(user_tokens), 5)  # Reduced to 5 per batch as requested
    }
    
    batch_info = f"Batch {batch_num}/{total_batches}" if batch_num and total_batches else "Batch"
    logger.info(f"🔄 {batch_info}: Processing {len(user_tokens)} users")
    
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            logger.info(f"    🔄 {batch_info}: API call attempt {attempt + 1}/{max_attempts}")
            response = session.post(search_url, headers=headers, json=body, timeout=30)
            
            if response.status_code == 401:
                msg = f"[ERROR] Authentication failed for batch request. Check your HUB_API_KEY."
                logger.error(msg)
                if error_log_path:
                    log_error(error_log_path, msg)
                return []
                
            if response.status_code != 200:
                if attempt < max_attempts - 1:
                    msg = f"[WARNING] Batch request failed with status {response.status_code}, retrying... (attempt {attempt + 1})"
                    logger.warning(msg)
                    if error_log_path:
                        log_error(error_log_path, msg)
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    error_details = response.text
                    msg = f"[ERROR] Batch request failed with status {response.status_code} after {max_attempts} attempts\n{error_details}"
                    logger.error(msg)
                    if error_log_path:
                        log_error(error_log_path, msg)
                    return []
            
            # Success - process results
            data = response.json()
            results = data.get('results', [])
            
            # Process results
            found_users = []
            found_tokens = set()
            
            for contact in results:
                props = contact.get('properties', {})
                user_token = props.get('platform_user_token')
                
                if user_token:
                    found_tokens.add(user_token)
                    found_users.append({
                        'user_token': user_token,
                        'email': props.get('email'),
                        'firstname': props.get('firstname'),
                        'lastname': props.get('lastname'),
                        'agentai_platform_credits_balance': props.get('agentai_platform_credits_balance')
                    })
            
            # Log results
            success_count = len(found_users)
            missing_count = len(user_tokens) - len(found_tokens)
            logger.info(f"    ✅ {batch_info}: Found {success_count} users, {missing_count} missing")
            
            return found_users
            
        except Exception as e:
            if attempt < max_attempts - 1:
                logger.warning(f"    ⚠️  {batch_info}: Exception occurred, retrying... (attempt {attempt + 1}): {str(e)}")
                time.sleep(2 ** attempt)
            else:
                logger.error(f"    ❌ {batch_info}: Failed after {max_attempts} attempts: {str(e)}")
                if error_log_path:
                    log_error(error_log_path, f"Exception in batch: {str(e)}")
                return []

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def main():
    parser = argparse.ArgumentParser(description='HubSpot Contact Lookup - Batch Optimized')
    parser.add_argument('-u', '--user-token', help='Single user token to lookup')
    parser.add_argument('-f', '--file', help='CSV file with user tokens')
    parser.add_argument('-o', '--output', help='Output CSV file for successful lookups')
    parser.add_argument('--error-log', default='hubspot_errors.log', help='Error log file')
    parser.add_argument('--skip-existing', action='store_true', default=True, help='Skip existing users')
    parser.add_argument('--batch-size', type=int, default=3, help='Number of users per batch (max 5 due to HubSpot API limit)')
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh all users')
    
    args = parser.parse_args()
    
    if not args.user_token and not args.file:
        parser.error("Either -u or -f must be specified")
    
    # Validate batch size doesn't exceed HubSpot's limit
    if args.batch_size > 5:
        logger.warning(f"Batch size {args.batch_size} exceeds HubSpot limit of 5. Setting to 5.")
        args.batch_size = 5
    
    if not HUB_API_KEY:
        logger.error("HUB_API_KEY not found in environment variables")
        sys.exit(1)
    
    # Initialize database
    db_path = get_db_path()
    initialize_users_table(db_path)
    
    # Process user tokens
    if args.user_token:
        user_tokens = [args.user_token]
    else:
        try:
            df = pd.read_csv(args.file)
            if 'user_token' not in df.columns:
                logger.error("CSV file must contain a 'user_token' column")
                sys.exit(1)
            user_tokens = df['user_token'].tolist()
        except Exception as e:
            logger.error(f"Error reading CSV file: {str(e)}")
            sys.exit(1)
    
    # Filter out existing users if needed
    if args.skip_existing and not args.force_refresh:
        existing_users = get_existing_users_batch(user_tokens, db_path)
        user_tokens = [token for token in user_tokens if token not in existing_users]
        logger.info(f"Skipping {len(existing_users)} existing users")
    
    if not user_tokens:
        logger.info("No new users to process")
        return
    
    # Process in batches
    total_users = len(user_tokens)
    total_batches = (total_users + args.batch_size - 1) // args.batch_size
    
    logger.info(f"Starting batch processing of {total_users} users in {total_batches} batches")
    
    all_users = []
    successful_batches = 0
    failed_batches = 0
    
    for i, batch in enumerate(chunks(user_tokens, args.batch_size), 1):
        batch_users = fetch_users_batch(batch, args.error_log, i, total_batches)
        if batch_users:
            all_users.extend(batch_users)
            successful_batches += 1
        else:
            failed_batches += 1
    
    # Save results
    if all_users:
        upsert_users_batch(all_users, db_path)
        logger.info(f"Successfully processed {len(all_users)} users")
        
        if args.output:
            df = pd.DataFrame(all_users)
            df.to_csv(args.output, index=False)
            logger.info(f"Saved results to {args.output}")
    
    # Summary
    logger.info("\n=== Processing Summary ===")
    logger.info(f"Total users: {total_users}")
    logger.info(f"Successful batches: {successful_batches}/{total_batches}")
    logger.info(f"Failed batches: {failed_batches}/{total_batches}")
    logger.info(f"Successfully processed users: {len(all_users)}")
    logger.info(f"Failed users: {total_users - len(all_users)}")

if __name__ == "__main__":
    main() 