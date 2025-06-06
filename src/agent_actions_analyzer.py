import sqlite3
import pandas as pd
import json
import sys
import os
from datetime import datetime

def initialize_db(db_path='data/agent_actions.db'):
    """Initialize the SQLite database with the required schema."""
    print(f"\nInitializing database at: {db_path}")
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        print(f"Ensuring directory exists: {os.path.dirname(db_path)}")
        
        conn = sqlite3.connect(db_path)
        print("Successfully connected to database")
        c = conn.cursor()
        
        print("Creating agent_actions table...")
        # Create the main agent_actions table
        c.execute('''
            CREATE TABLE IF NOT EXISTS agent_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                agent_name TEXT,
                user_token TEXT,
                action_type TEXT,
                llm_model TEXT,
                llm_model_prompt TEXT,
                message_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        print("Creating indices...")
        # Create indices for common query fields
        c.execute('CREATE INDEX IF NOT EXISTS idx_agent_id ON agent_actions(agent_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_action_type ON agent_actions(action_type)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_user_token ON agent_actions(user_token)')
        
        conn.commit()
        
        # Verify table creation
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = c.fetchall()
        print("\nTables in database:", [table[0] for table in tables])
        
        conn.close()
        print("Database initialization complete")
        
    except Exception as e:
        print(f"Error during database initialization: {str(e)}")
        if 'conn' in locals():
            conn.close()
        raise

def process_csv_file(csv_path, db_path='data/agent_actions.db'):
    """Process the CSV file and insert data into the SQLite database."""
    try:
        # Read CSV file
        print(f"\nReading CSV file: {csv_path}")
        df = pd.read_csv(csv_path)
        print(f"Found {len(df)} rows")
        
        # Print column names for verification
        print("\nCSV columns:", df.columns.tolist())
        
        # Connect to database
        print(f"\nConnecting to database: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verify table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_actions'")
        if not cursor.fetchone():
            raise Exception("agent_actions table not found in database!")
        
        # First, clear existing data to avoid duplicates
        cursor.execute('DELETE FROM agent_actions')
        print("Cleared existing data from database")
        
        # Process each row
        print("\nProcessing rows...")
        rows_processed = 0
        for idx, row in df.iterrows():
            if idx % 100 == 0:  # Progress indicator
                print(f"Processing row {idx}/{len(df)}")

            # Validate message_json if it exists
            message_json = row['message_json']
            if pd.notna(message_json) and isinstance(message_json, str):
                try:
                    # Verify it's valid JSON
                    json.loads(message_json)
                except json.JSONDecodeError:
                    print(f"\nWarning: Invalid JSON in row {idx}, setting to None")
                    message_json = None
            else:
                message_json = None

            try:
                # Insert data into database with correct column mapping
                cursor.execute('''
                    INSERT INTO agent_actions (
                        agent_id, agent_name, user_token, action_type,
                        llm_model, llm_model_prompt, message_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(row['agent_id']),
                    str(row['agent_name']),
                    str(row['user_token']),
                    str(row['action_type']),
                    str(row['llm_model']) if pd.notna(row['llm_model']) else None,
                    str(row['llm_model_prompt']) if pd.notna(row['llm_model_prompt']) else None,
                    message_json
                ))
                rows_processed += 1
            except Exception as e:
                print(f"\nError processing row {idx}:")
                print(f"Row data: {row.to_dict()}")
                print(f"Error: {str(e)}")
                raise
        
        # Commit changes
        print("\nCommitting changes...")
        conn.commit()
        
        # Verify the import
        print("\nVerifying import...")
        cursor.execute('SELECT COUNT(*) FROM agent_actions')
        count = cursor.fetchone()[0]
        print(f"Total rows in database: {count}")
        print(f"Rows processed: {rows_processed}")
        
        if count != rows_processed:
            print("WARNING: Number of rows in database doesn't match processed rows!")
        
        cursor.execute('SELECT DISTINCT action_type FROM agent_actions')
        action_types = cursor.fetchall()
        print("\nDistinct action types found:")
        for action_type in action_types:
            print(f"- {action_type[0]}")
        
        # Sample verification
        print("\nSample of inserted data:")
        cursor.execute('SELECT * FROM agent_actions LIMIT 3')
        sample = cursor.fetchall()
        for row in sample:
            print(row)
        
        conn.close()
        print("\nDatabase processing complete!")
        
    except Exception as e:
        print(f"\nError processing CSV file: {str(e)}")
        if 'conn' in locals():
            conn.close()
        raise

def main():
    """Main function to handle command line arguments and process the CSV file."""
    if len(sys.argv) != 2:
        print("Usage: python agent_actions_analyzer.py <csv_file_path>")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    if not os.path.exists(csv_file_path):
        print(f"Error: File {csv_file_path} not found")
        sys.exit(1)
    
    try:
        print("\n=== Starting Database Initialization ===")
        initialize_db()
        
        print("\n=== Starting CSV Processing ===")
        process_csv_file(csv_file_path)
        
        print("\n=== Processing Complete ===")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 