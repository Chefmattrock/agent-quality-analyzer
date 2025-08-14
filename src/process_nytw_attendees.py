#!/usr/bin/env python3
"""
Process NYTW attendees and update the users table with their status and associated agents.
"""

import os
import sys
import pandas as pd
import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('nytw_processing.log')
    ]
)
logger = logging.getLogger(__name__)

def get_project_root():
    """Get the project root directory."""
    script_dir = Path(__file__).parent.absolute()
    return script_dir.parent

def get_db_path():
    """Get the database path."""
    project_root = get_project_root()
    return str(project_root / 'data' / 'agents.db')

def validate_csv(df: pd.DataFrame) -> bool:
    """Validate the CSV data has required columns."""
    required_columns = [
        "Record ID - Contact",
        "First Name",
        "Last Name",
        "Email",
        "Platform User Token",
        "Last Activity Date",
        "Record ID - Company",
        "Company name"
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        return False
    
    # Check for empty platform tokens
    empty_tokens = df['Platform User Token'].isna().sum()
    if empty_tokens > 0:
        logger.warning(f"Found {empty_tokens} rows with empty platform tokens")
    
    return True

def get_user_agents(user_token: str, conn: sqlite3.Connection) -> List[Dict]:
    """Get all agents (public and private) associated with a user's platform token."""
    cursor = conn.cursor()
    
    # Query both public and private agents
    cursor.execute("""
        SELECT agent_id, agent_id_human, name, authors, status
        FROM agents
        WHERE EXISTS (
            SELECT 1 FROM json_each(authors) 
            WHERE json_each.key = ?
        )
    """, (user_token,))
    
    agents = []
    for row in cursor.fetchall():
        agent_id, agent_id_human, name, authors_json, status = row
        agents.append({
            'agent_id': agent_id,
            'agent_id_human': agent_id_human,
            'name': name,
            'status': status
        })
    
    return agents

def init_db(conn: sqlite3.Connection):
    """Initialize database schema if needed."""
    cursor = conn.cursor()
    
    # Check if nytw_status column exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Add nytw_status column if it doesn't exist
    if 'nytw_status' not in columns:
        logger.info("Adding nytw_status column to users table")
        cursor.execute("ALTER TABLE users ADD COLUMN nytw_status TEXT")
    
    # Add agents column if it doesn't exist
    if 'agents' not in columns:
        logger.info("Adding agents column to users table")
        cursor.execute("ALTER TABLE users ADD COLUMN agents TEXT")
    
    conn.commit()

def process_attendees(csv_path: str, batch_size: int = 50):
    """Process NYTW attendees and update the database."""
    logger.info(f"Starting NYTW attendee processing from {csv_path}")
    
    # Read and validate CSV
    try:
        df = pd.read_csv(csv_path)
        if not validate_csv(df):
            logger.error("CSV validation failed")
            return
    except Exception as e:
        logger.error(f"Error reading CSV: {str(e)}")
        return
    
    # Connect to database and initialize schema
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    init_db(conn)
    
    # Initialize counters
    total_attendees = len(df)
    processed = 0
    updated = 0
    unmatched = []
    no_agents = []
    
    # Process in batches
    for i in range(0, total_attendees, batch_size):
        batch = df.iloc[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1} ({i+1}-{min(i+batch_size, total_attendees)} of {total_attendees})")
        
        for _, row in batch.iterrows():
            email = row['Email']
            platform_token = row['Platform User Token']
            
            if pd.isna(platform_token):
                unmatched.append(email)
                logger.warning(f"No platform token found for email: {email}")
                continue
                
            # Get user's agents
            agents = get_user_agents(platform_token, conn)
            
            if agents:
                # Update user record
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET nytw_status = 'confirmed',
                        agents = ?
                    WHERE user_token = ?
                """, (json.dumps(agents), platform_token))
                
                if cursor.rowcount > 0:
                    updated += 1
                    logger.info(f"Updated user {email} ({platform_token}) with {len(agents)} agents")
                else:
                    # Try to insert if update failed
                    cursor.execute("""
                        INSERT INTO users (user_token, email, nytw_status, agents)
                        VALUES (?, ?, 'confirmed', ?)
                    """, (platform_token, email, json.dumps(agents)))
                    if cursor.rowcount > 0:
                        updated += 1
                        logger.info(f"Inserted new user {email} ({platform_token}) with {len(agents)} agents")
                    else:
                        unmatched.append(email)
                        logger.warning(f"Failed to insert/update user: {email} ({platform_token})")
            else:
                no_agents.append(email)
                logger.warning(f"No agents found for user: {email} ({platform_token})")
            
            processed += 1
        
        # Commit after each batch
        conn.commit()
    
    # Log summary
    logger.info("\n=== Processing Summary ===")
    logger.info(f"Total attendees processed: {processed}")
    logger.info(f"Users updated/inserted: {updated}")
    logger.info(f"Users with no platform token: {len(unmatched)}")
    logger.info(f"Users with no agents: {len(no_agents)}")
    
    # Save unmatched emails to file
    if unmatched:
        unmatched_file = 'unmatched_nytw_attendees.txt'
        with open(unmatched_file, 'w') as f:
            for email in unmatched:
                f.write(f"{email}\n")
        logger.info(f"Saved unmatched emails to {unmatched_file}")
    
    # Save users with no agents to file
    if no_agents:
        no_agents_file = 'data/nytw_attendees_no_agents.txt'
        with open(no_agents_file, 'w') as f:
            for email in no_agents:
                f.write(f"{email}\n")
        logger.info(f"Saved users with no agents to {no_agents_file}")
    
    conn.close()

def main():
    if len(sys.argv) != 2:
        print("Usage: python process_nytw_attendees.py <path_to_nytw_attendees.csv>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        sys.exit(1)
    
    process_attendees(csv_path)

if __name__ == "__main__":
    main() 