#!/usr/bin/env python3
"""
Export Agents Query Results to CSV
"""

import sqlite3
import pandas as pd

def export_agents_to_csv(output_file="data/top_agents_by_executions.csv"):
    """Export agents query results to CSV file"""
    
    # Connect to database
    conn = sqlite3.connect('data/agents.db')
    
    # Execute query
    query = """
    SELECT name, executions, agent_id, tags, reviews_count, reviews_score, description 
    FROM agents 
    WHERE executions IS NOT NULL 
    ORDER BY executions DESC;
    """
    
    # Read into DataFrame
    df = pd.read_sql_query(query, conn)
    
    # Close connection
    conn.close()
    
    # Export to CSV
    df.to_csv(output_file, index=False)
    
    print(f"✅ Exported {len(df)} agents to {output_file}")
    print(f"📊 Top 5 agents by executions:")
    print(df[['name', 'executions']].head())

if __name__ == "__main__":
    export_agents_to_csv() 