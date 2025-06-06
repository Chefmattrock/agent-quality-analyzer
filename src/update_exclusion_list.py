#!/usr/bin/env python3
"""
Update Paid Traffic Exclusion List

PURPOSE:
Removes Grant Program Builder agents from the paid traffic exclusion list
since they should be classified as Group A, not excluded from Group C.
"""

import sqlite3
import pandas as pd

def update_exclusion_list():
    """Remove Grant Program Builder agents from paid traffic exclusion list."""
    
    print("🔄 Updating paid traffic exclusion list...")
    
    # Load current exclusion list
    df = pd.read_csv('paid_traffic_exclusion_list.csv')
    original_count = len(df)
    print(f"Original exclusion list: {original_count} agents")
    
    # Connect to database
    db_path = 'data/agents.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all Grant Program Builder agent IDs
    cursor.execute("SELECT agent_id FROM agents WHERE builder_grant_program = 1")
    grant_program_agent_ids = set([row[0] for row in cursor.fetchall()])
    
    print(f"Grant Program Builder agents: {len(grant_program_agent_ids)}")
    
    # Find overlap
    exclusion_agent_ids = set(df['agent_id'].tolist())
    overlap = exclusion_agent_ids.intersection(grant_program_agent_ids)
    
    print(f"Grant Program Builder agents in exclusion list: {len(overlap)}")
    if overlap:
        print("Overlapping agents:")
        for agent_id in overlap:
            cursor.execute("SELECT name FROM agents WHERE agent_id = ?", (agent_id,))
            result = cursor.fetchone()
            name = result[0] if result else "Unknown"
            print(f"   {agent_id} - {name}")
    
    # Remove Grant Program Builder agents from exclusion list
    filtered_df = df[~df['agent_id'].isin(grant_program_agent_ids)]
    
    print(f"\nRemoving {original_count - len(filtered_df)} Grant Program Builder agents from exclusion list")
    print(f"Updated exclusion list: {len(filtered_df)} agents")
    
    # Save updated exclusion list
    filtered_df.to_csv('paid_traffic_exclusion_list.csv', index=False)
    print("✅ Updated paid_traffic_exclusion_list.csv")
    
    conn.close()
    
    return len(overlap)

if __name__ == "__main__":
    removed_count = update_exclusion_list()
    print(f"\n🎯 Removed {removed_count} Grant Program Builder agents from paid traffic exclusion list")
    print("Ready to re-run three group comparison analysis!") 