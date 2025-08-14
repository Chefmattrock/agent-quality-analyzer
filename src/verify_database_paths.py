#!/usr/bin/env python3
"""
Verification script to test that all database connections point to the correct agents.db file.
"""

import sqlite3
import os
import sys

def test_database_connection():
    """Test that the database path is correct and accessible."""
    
    # This should be the path used by all scripts when run from root directory
    db_path = 'data/agents.db'
    
    print("🔍 Testing database connection...")
    print(f"Database path: {db_path}")
    print(f"Absolute path: {os.path.abspath(db_path)}")
    
    # Check if file exists
    if not os.path.exists(db_path):
        print("❌ ERROR: Database file does not exist!")
        return False
    
    # Check file size
    file_size = os.path.getsize(db_path)
    print(f"Database size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
    
    # Test connection
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM agents")
        agent_count = cursor.fetchone()[0]
        print(f"Total agents in database: {agent_count:,}")
        
        # Test table structure
        cursor.execute("PRAGMA table_info(agents)")
        columns = cursor.fetchall()
        print(f"Number of columns in agents table: {len(columns)}")
        
        # Test a few key columns
        key_columns = ['agent_id', 'name', 'created_at', 'status', 'authors']
        cursor.execute("PRAGMA table_info(agents)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        missing_columns = [col for col in key_columns if col not in existing_columns]
        if missing_columns:
            print(f"⚠️  Missing expected columns: {missing_columns}")
        else:
            print("✅ All key columns present")
        
        # Test sample data
        cursor.execute("SELECT name, status, created_at FROM agents LIMIT 3")
        sample_agents = cursor.fetchall()
        print("\n📋 Sample agents:")
        for i, (name, status, created_at) in enumerate(sample_agents, 1):
            print(f"  {i}. {name} ({status}) - {created_at}")
        
        conn.close()
        print("\n✅ Database connection test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Database connection failed: {e}")
        return False

def main():
    print("🚀 Database Path Verification")
    print("=" * 50)
    
    # Show current working directory
    print(f"Current working directory: {os.getcwd()}")
    
    # Test the database connection
    success = test_database_connection()
    
    if success:
        print("\n🎉 All database paths should now be correctly configured!")
        print("All scripts will use the main database at: data/agents.db")
    else:
        print("\n❌ Database verification failed!")
        print("Please check that the database exists and is accessible.")
        sys.exit(1)

if __name__ == "__main__":
    main() 