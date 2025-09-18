#!/usr/bin/env python3
"""
DuckDB setup script for agent runs data migration
Imports CSV data with JSON columns for efficient querying
"""

import duckdb
import pandas as pd
import sys
import os
from datetime import datetime

def setup_duckdb_database():
    """Set up DuckDB database and import CSV data"""
    
    print("🦆 Setting up DuckDB database for agent runs analysis")
    print("=" * 60)
    
    # Database file path
    db_path = 'data/agent_runs.duckdb'
    csv_path = 'data/public_agent_latest_runs.csv'
    
    # Check if CSV exists
    if not os.path.exists(csv_path):
        print(f"❌ Error: CSV file not found at {csv_path}")
        return False
    
    print(f"📄 CSV file: {csv_path}")
    print(f"💾 Database: {db_path}")
    
    try:
        # Connect to DuckDB (creates file if it doesn't exist)
        conn = duckdb.connect(db_path)
        print(f"✅ Connected to DuckDB database")
        
        # Create the table with proper schema
        print("📋 Creating table schema...")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_runs (
                agent_id VARCHAR,
                name VARCHAR,
                total_runs_30d INTEGER,
                run_id VARCHAR PRIMARY KEY,
                user_token VARCHAR,
                run_started_at TIMESTAMP,
                run_completed_at TIMESTAMP,
                total_steps INTEGER,
                response JSON
            )
        """)
        
        # Import CSV data using pandas (handles large JSON better)
        print("📥 Reading CSV with pandas (handling large JSON rows)...")
        start_time = datetime.now()
        
        # Read CSV in chunks to handle memory efficiently
        chunk_size = 100
        total_rows = 0
        
        for chunk_num, df_chunk in enumerate(pd.read_csv(csv_path, chunksize=chunk_size)):
            print(f"   Processing chunk {chunk_num + 1} ({len(df_chunk)} rows)...")
            
            # Insert chunk into DuckDB
            conn.register('temp_chunk', df_chunk)
            conn.execute("INSERT INTO agent_runs SELECT * FROM temp_chunk")
            conn.unregister('temp_chunk')
            
            total_rows += len(df_chunk)
        
        print(f"✅ Processed {total_rows} rows total")
        
        import_time = datetime.now() - start_time
        print(f"✅ Import completed in {import_time.total_seconds():.2f} seconds")
        
        # Get basic stats
        result = conn.execute("SELECT COUNT(*) as total_rows FROM agent_runs").fetchone()
        final_row_count = result[0]
        print(f"📊 Final database contains {final_row_count:,} rows")
        
        # Test JSON functionality
        print("🧪 Testing JSON query functionality...")
        test_result = conn.execute("""
            SELECT COUNT(*) as json_test
            FROM agent_runs 
            WHERE json_extract(response, '$.step-1') IS NOT NULL
        """).fetchone()
        
        json_rows = test_result[0]
        print(f"✅ Found {json_rows:,} rows with JSON step-1 data")
        
        # Show sample of available JSON paths
        print("🔍 Sample JSON structure analysis...")
        sample_paths = conn.execute("""
            SELECT 
                json_extract(response, '$.step-1.engine') as step1_engine,
                json_extract(response, '$.step-2.engine') as step2_engine,
                json_extract(response, '$.step-3.engine') as step3_engine
            FROM agent_runs 
            WHERE response IS NOT NULL 
            LIMIT 5
        """).fetchall()
        
        print("Sample engines found:")
        for i, row in enumerate(sample_paths, 1):
            print(f"  Row {i}: {row}")
        
        conn.close()
        print(f"\n🎉 DuckDB setup completed successfully!")
        print(f"Database saved to: {db_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error during setup: {str(e)}")
        return False

def show_usage_examples():
    """Show example queries for the new DuckDB database"""
    print("\n" + "=" * 60)
    print("📚 USAGE EXAMPLES")
    print("=" * 60)
    
    examples = [
        ("Basic agent stats", """
SELECT agent_id, name, total_runs_30d, total_steps
FROM agent_runs 
ORDER BY total_runs_30d DESC 
LIMIT 10;
        """),
        
        ("Extract step engines", """
SELECT 
    agent_id, 
    name,
    json_extract(response, '$.step-1.engine') as first_engine,
    json_extract(response, '$.step-2.engine') as second_engine
FROM agent_runs 
WHERE response IS NOT NULL
LIMIT 10;
        """),
        
        ("Token usage analysis", """
SELECT 
    agent_id,
    name,
    json_extract(response, '$.step-2.metadata.usage.total_tokens') as tokens
FROM agent_runs 
WHERE json_extract(response, '$.step-2.metadata.usage.total_tokens') IS NOT NULL
ORDER BY CAST(json_extract(response, '$.step-2.metadata.usage.total_tokens') AS INTEGER) DESC
LIMIT 10;
        """),
        
        ("Find runs by specific engine", """
SELECT COUNT(*) as deepseek_runs
FROM agent_runs 
WHERE json_extract(response, '$.step-2.engine') LIKE '%deepseek%';
        """),
        
        ("Execution time analysis", """
SELECT 
    agent_id,
    name,
    run_started_at,
    run_completed_at,
    EXTRACT(EPOCH FROM (run_completed_at - run_started_at)) as duration_seconds
FROM agent_runs 
WHERE run_completed_at IS NOT NULL 
    AND run_started_at IS NOT NULL
ORDER BY duration_seconds DESC
LIMIT 10;
        """)
    ]
    
    for title, query in examples:
        print(f"\n🔍 {title}:")
        print(query.strip())
    
    print(f"\n💡 To run these queries:")
    print(f"   python -c \"import duckdb; conn=duckdb.connect('data/agent_runs.duckdb'); print(conn.execute('YOUR_QUERY').fetchall())\"")

if __name__ == "__main__":
    success = setup_duckdb_database()
    if success:
        show_usage_examples()
    else:
        sys.exit(1)
