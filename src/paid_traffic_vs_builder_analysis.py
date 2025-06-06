#!/usr/bin/env python3
"""
Paid Traffic vs Builder Grant Program Analysis

PURPOSE:
Find how many agents that received paid traffic are NOT part of the builder grant program.

WHAT IT DOES:
1. Loads the list of agents that received paid traffic (69 agents)
2. Cross-references with builder grant program agents
3. Counts overlap and non-overlap
"""

import os
import sqlite3
import pandas as pd

def analyze_paid_traffic_vs_builder():
    """Analyze overlap between paid traffic agents and builder grant program."""
    
    # Load paid traffic agents
    if not os.path.exists('paid_traffic_exclusion_list.csv'):
        print("❌ paid_traffic_exclusion_list.csv not found. Run find_paid_traffic_agents.py first.")
        return
    
    paid_traffic_df = pd.read_csv('paid_traffic_exclusion_list.csv')
    paid_traffic_ids = set(paid_traffic_df['agent_id'].tolist())
    
    # Connect to database
    db_path = 'data/agents.db' if os.path.exists('data/agents.db') else '../data/agents.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if builder_grant_program column exists
    cursor.execute("PRAGMA table_info(agents)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'builder_grant_program' not in columns:
        print("❌ builder_grant_program column not found. Run list_301_analysis.py first.")
        conn.close()
        return
    
    # Get builder grant program agent IDs
    cursor.execute("SELECT agent_id FROM agents WHERE builder_grant_program = 1")
    builder_ids = set([row[0] for row in cursor.fetchall()])
    
    # Find overlap and non-overlap
    paid_traffic_and_builder = paid_traffic_ids.intersection(builder_ids)
    paid_traffic_not_builder = paid_traffic_ids - builder_ids
    
    # Get details for reporting
    cursor.execute("""
        SELECT agent_id, agent_id_human, name, status, executions, reviews_count, price
        FROM agents 
        WHERE agent_id IN ({})
    """.format(','.join(['?' for _ in paid_traffic_not_builder])), list(paid_traffic_not_builder))
    
    non_builder_details = cursor.fetchall()
    
    cursor.execute("""
        SELECT agent_id, agent_id_human, name, status, executions, reviews_count, price
        FROM agents 
        WHERE agent_id IN ({})
    """.format(','.join(['?' for _ in paid_traffic_and_builder])), list(paid_traffic_and_builder))
    
    builder_details = cursor.fetchall()
    
    conn.close()
    
    # Display results
    print("🔍 Paid Traffic vs Builder Grant Program Analysis")
    print("=" * 60)
    print(f"Total agents that received paid traffic: {len(paid_traffic_ids)}")
    print(f"Total builder grant program agents: {len(builder_ids)}")
    print()
    print(f"🎯 MAIN ANSWER:")
    print(f"Paid traffic agents NOT in builder program: {len(paid_traffic_not_builder)}")
    print()
    print(f"📈 BREAKDOWN:")
    print(f"├── Paid traffic agents that ARE in builder program: {len(paid_traffic_and_builder)}")
    print(f"└── Paid traffic agents that are NOT in builder program: {len(paid_traffic_not_builder)}")
    print()
    
    # Calculate percentages
    if len(paid_traffic_ids) > 0:
        pct_not_builder = (len(paid_traffic_not_builder) / len(paid_traffic_ids)) * 100
        pct_builder = (len(paid_traffic_and_builder) / len(paid_traffic_ids)) * 100
        print(f"💹 PERCENTAGES OF PAID TRAFFIC AGENTS:")
        print(f"├── {pct_not_builder:.1f}% are NOT in builder program")
        print(f"└── {pct_builder:.1f}% are in builder program")
        print()
    
    # Show agents that are in both programs
    if builder_details:
        print(f"✅ PAID TRAFFIC AGENTS ALSO IN BUILDER PROGRAM ({len(builder_details)}):")
        print(f"{'Agent ID':<15} {'Name':<40} {'Executions':<12} {'Reviews'}")
        print("-" * 80)
        for agent in builder_details:
            agent_id = agent[1] or agent[0]  # Use human_id if available
            name = (agent[2] or "No name")[:39]  # Truncate long names
            executions = agent[4] or 0
            reviews = agent[5] or 0
            print(f"{agent_id:<15} {name:<40} {executions:<12} {reviews}")
        print()
    
    # Show some examples of non-builder paid traffic agents
    if non_builder_details:
        print(f"❌ PAID TRAFFIC AGENTS NOT IN BUILDER PROGRAM (first 10 of {len(non_builder_details)}):")
        print(f"{'Agent ID':<15} {'Name':<40} {'Executions':<12} {'Reviews'}")
        print("-" * 80)
        for i, agent in enumerate(non_builder_details[:10]):
            agent_id = agent[1] or agent[0]  # Use human_id if available
            name = (agent[2] or "No name")[:39]  # Truncate long names
            executions = agent[4] or 0
            reviews = agent[5] or 0
            print(f"{agent_id:<15} {name:<40} {executions:<12} {reviews}")
        
        if len(non_builder_details) > 10:
            print(f"... and {len(non_builder_details) - 10} more")

def main():
    analyze_paid_traffic_vs_builder()

if __name__ == "__main__":
    main() 