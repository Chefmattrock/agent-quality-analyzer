#!/usr/bin/env python3
"""
Simple script to refresh local data by:
1. Fetching latest public agents from agent.ai API
2. Updating HubSpot contact data for all users found in the agents database
"""

import os
import sys
import subprocess
import sqlite3
import json
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Command failed with exit code {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def get_unique_user_tokens():
    """Extract unique user tokens from the agents database."""
    db_path = 'data/agents.db'
    if not os.path.exists(db_path):
        print(f"ERROR: Database {db_path} does not exist")
        return []
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Get all authors JSON from agents table
    c.execute("SELECT authors FROM agents WHERE authors IS NOT NULL AND authors != ''")
    results = c.fetchall()
    conn.close()
    
    user_tokens = set()
    for (authors_json,) in results:
        try:
            authors = json.loads(authors_json)
            # Extract user_token keys from the authors dictionary
            user_tokens.update(authors.keys())
        except json.JSONDecodeError:
            continue
    
    return list(user_tokens)

def create_temp_user_tokens_csv(user_tokens):
    """Create a temporary CSV file with user tokens."""
    import pandas as pd
    temp_file = 'temp_user_tokens.csv'
    df = pd.DataFrame({'user_token': user_tokens})
    df.to_csv(temp_file, index=False)
    return temp_file

def main():
    print("🚀 Starting data refresh process...")
    
    # Change to the src directory for running scripts
    original_dir = os.getcwd()
    src_dir = Path(original_dir) / 'src'
    
    if not src_dir.exists():
        print("ERROR: src directory not found")
        sys.exit(1)
    
    os.chdir(src_dir)
    
    try:
        # Step 1: Fetch public agents
        success = run_command(
            ['python', 'agent_finder.py', '-p', 'public', '-n', '100'],
            "Fetching public agents from agent.ai API"
        )
        
        if not success:
            print("❌ Failed to fetch agents. Aborting.")
            return
        
        # Step 2: Get user tokens from the database
        os.chdir(original_dir)  # Back to root for database access
        print(f"\n{'='*60}")
        print("Extracting user tokens from agents database...")
        print(f"{'='*60}")
        
        user_tokens = get_unique_user_tokens()
        if not user_tokens:
            print("⚠️  No user tokens found in database. Skipping HubSpot lookup.")
            return
        
        print(f"Found {len(user_tokens)} unique user tokens")
        
        # Step 3: Create temp CSV file with user tokens
        temp_csv = create_temp_user_tokens_csv(user_tokens)
        print(f"Created temporary file: {temp_csv}")
        
        # Step 4: Batch lookup HubSpot contacts
        os.chdir(src_dir)
        success = run_command(
            ['python', 'hubspot_contact_lookup.py', '-f', f'../{temp_csv}'],
            "Looking up HubSpot contact data for all users"
        )
        
        # Cleanup temp file
        os.chdir(original_dir)
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
            print(f"Cleaned up temporary file: {temp_csv}")
        
        if success:
            print(f"\n🎉 Data refresh completed successfully!")
            print("✅ Public agents updated")
            print("✅ HubSpot contact data updated")
        else:
            print("\n⚠️  Data refresh completed with errors in HubSpot lookup")
            print("✅ Public agents updated")
            print("❌ HubSpot contact data had errors")
            
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        # Ensure we're back in the original directory
        os.chdir(original_dir)

if __name__ == "__main__":
    main() 