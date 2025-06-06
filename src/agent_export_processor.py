import sqlite3
import pandas as pd
import sys
import os
from datetime import datetime
import csv

def initialize_db(db_path='data/agents-may.db'):
    """Initialize the SQLite database with the required schema."""
    print(f"\nInitializing database at: {db_path}")
    try:
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        print(f"Ensuring directory exists: {os.path.dirname(db_path)}")
        
        conn = sqlite3.connect(db_path)
        print("Successfully connected to database")
        c = conn.cursor()
        
        print("Creating agents table...")
        c.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                agent_id_human TEXT,
                type TEXT,
                version TEXT,
                name TEXT,
                description TEXT,
                status TEXT,
                demo_video_url TEXT,
                user_token TEXT,
                is_open INTEGER,
                is_approved INTEGER,
                marketplace_approved_at TEXT,
                executions INTEGER,
                email_alias TEXT,
                cron TEXT,
                trigger TEXT,
                trigger2 TEXT,
                codeSharing TEXT,
                shareSetting TEXT,
                open_sourced_at TEXT,
                enable_generating_shareable_urls INTEGER,
                enable_agent_actions_caching INTEGER,
                external_url TEXT,
                reviews_count INTEGER,
                reviews_score REAL,
                created_at TEXT,
                updated_at TEXT,
                enable_read_only INTEGER
            )
        ''')
        conn.commit()
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

def process_csv_file(csv_path, db_path='data/agents-may.db'):
    """Process the TSV file and insert data into the SQLite database."""
    try:
        print(f"\nReading TSV file: {csv_path}")
        df = pd.read_csv(
            csv_path,
            sep='\t',
            quoting=csv.QUOTE_MINIMAL,
            quotechar='"',
            escapechar='\\',
            dtype=str,
            on_bad_lines='warn'  # For pandas >=1.3.0
        )
        print("DataFrame shape:", df.shape)
        print("DataFrame columns:", df.columns.tolist())
        df = df.loc[:, ~df.columns.str.match('^Unnamed')]
        expected_columns = [
            'agent_id', 'agent_id_human', 'type', 'version', 'name', 'description', 'status', 'demo_video_url',
            'user_token', 'is_open', 'is_approved', 'marketplace_approved_at', 'executions', 'email_alias', 'cron',
            'trigger', 'trigger2', 'codeSharing', 'shareSetting', 'open_sourced_at', 'enable_generating_shareable_urls',
            'enable_agent_actions_caching', 'external_url', 'reviews_count', 'reviews_score', 'created_at', 'updated_at',
            'enable_read_only'
        ]
        print(f"DataFrame columns: {df.columns.tolist()}")
        print(f"Expected columns: {expected_columns}")
        print(f"Extra columns: {set(df.columns) - set(expected_columns)}")
        print(f"Missing columns: {set(expected_columns) - set(df.columns)}")
        df = df[[col for col in expected_columns if col in df.columns]]
        extra_cols = set(df.columns) - set(expected_columns)
        if extra_cols:
            print("Dropping extra columns:", extra_cols)
            df = df.drop(columns=list(extra_cols))
        print("Final DataFrame shape:", df.shape)
        print("Final DataFrame columns:", df.columns.tolist())
        print(f"Found {len(df)} rows")
        print("\nTSV columns:", df.columns.tolist())
        print(f"\nConnecting to database: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agents'")
        if not cursor.fetchone():
            raise Exception("agents table not found in database!")
        cursor.execute('DELETE FROM agents')
        print("Cleared existing data from database")
        print("\nProcessing rows...")
        rows_processed = 0
        rows_skipped = 0
        for idx, row in df.iterrows():
            if idx % 100 == 0:
                print(f"Processing row {idx}/{len(df)}")
            try:
                insert_tuple = (
                    row.get('agent_id'),
                    row.get('agent_id_human'),
                    row.get('type'),
                    row.get('version'),
                    row.get('name'),
                    row.get('description'),
                    row.get('status'),
                    row.get('demo_video_url'),
                    row.get('user_token'),
                    safe_int(row.get('is_open')),
                    safe_int(row.get('is_approved')),
                    row.get('marketplace_approved_at'),
                    safe_int(row.get('executions')),
                    row.get('email_alias'),
                    row.get('cron'),
                    row.get('trigger'),
                    row.get('trigger2'),
                    row.get('codeSharing'),
                    row.get('shareSetting'),
                    row.get('open_sourced_at'),
                    safe_int(row.get('enable_generating_shareable_urls')),
                    safe_int(row.get('enable_agent_actions_caching')),
                    row.get('external_url'),
                    safe_int(row.get('reviews_count')),
                    safe_float(row.get('reviews_score')),
                    row.get('created_at'),
                    row.get('updated_at'),
                    safe_int(row.get('enable_read_only'))
                )
                cursor.execute('''
                    INSERT OR REPLACE INTO agents (
                        agent_id, agent_id_human, type, version, name, description, status, demo_video_url, user_token, is_open, is_approved, marketplace_approved_at, executions, email_alias, cron, trigger, trigger2, codeSharing, shareSetting, open_sourced_at, enable_generating_shareable_urls, enable_agent_actions_caching, external_url, reviews_count, reviews_score, created_at, updated_at, enable_read_only
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', insert_tuple)
                rows_processed += 1
            except Exception as e:
                print(f"\nSkipping row {idx} due to error:")
                print(f"Row data: {row.to_dict()}")
                print(f"Error: {str(e)}")
                rows_skipped += 1
        print(f"\nCommitting changes...")
        conn.commit()
        print(f"\nVerifying import...")
        cursor.execute('SELECT COUNT(*) FROM agents')
        count = cursor.fetchone()[0]
        print(f"Total rows in database: {count}")
        print(f"Rows processed: {rows_processed}")
        print(f"Rows skipped: {rows_skipped}")
        if count != rows_processed:
            print("WARNING: Number of rows in database doesn't match processed rows!")
        cursor.execute('SELECT DISTINCT status FROM agents')
        statuses = cursor.fetchall()
        print("\nDistinct statuses found:")
        for status in statuses:
            print(f"- {status[0]}")
        print("\nSample of inserted data:")
        cursor.execute('SELECT * FROM agents LIMIT 3')
        sample = cursor.fetchall()
        for row in sample:
            print(row)
        conn.close()
        print("\nDatabase processing complete!")
    except Exception as e:
        print(f"\nError processing TSV file: {str(e)}")
        if 'conn' in locals():
            conn.close()
        raise

def safe_int(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return None

def safe_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def main():
    if len(sys.argv) != 2:
        print("Usage: python agent_export_processor.py <tsv_file_path>")
        sys.exit(1)
    tsv_file_path = sys.argv[1]
    if not os.path.exists(tsv_file_path):
        print(f"Error: File {tsv_file_path} not found")
        sys.exit(1)
    try:
        print("\n=== Starting Database Initialization ===")
        initialize_db()
        print("\n=== Starting TSV Processing ===")
        process_csv_file(tsv_file_path)
        print("\n=== Processing Complete ===")
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 