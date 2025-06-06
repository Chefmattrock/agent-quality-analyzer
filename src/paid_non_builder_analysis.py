#!/usr/bin/env python3
"""
Paid Non-Builder Program Agent Analysis

PURPOSE:
This script analyzes how many agents are in the paid list that are not part of the builder program.

WHAT IT DOES:
1. Connects to the agents database
2. Counts agents with price > 0 (paid agents)
3. Counts paid agents that are NOT marked as builder_grant_program = 1
4. Provides a breakdown of the results
"""

import os
import sqlite3
import pandas as pd

def analyze_paid_non_builder_agents():
    """Analyze paid agents that are not part of the builder program."""
    # Determine the correct database path
    db_path = 'data/agents.db' if os.path.exists('data/agents.db') else '../data/agents.db'
    
    if not os.path.exists(db_path):
        print("Error: Cannot find agents.db database")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Analyzing Paid Agents vs Builder Program")
    print("=" * 60)
    
    # Check if builder_grant_program column exists
    cursor.execute("PRAGMA table_info(agents)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'builder_grant_program' not in columns:
        print("❌ builder_grant_program column not found in database.")
        print("   Please run the Grant Program Builders analysis first.")
        conn.close()
        return
    
    # Count total agents
    cursor.execute("SELECT COUNT(*) FROM agents")
    total_agents = cursor.fetchone()[0]
    
    # Count paid agents (price > 0)
    cursor.execute("SELECT COUNT(*) FROM agents WHERE price > 0")
    total_paid_agents = cursor.fetchone()[0]
    
    # Count free agents (price = 0 or NULL)
    cursor.execute("SELECT COUNT(*) FROM agents WHERE price IS NULL OR price = 0")
    total_free_agents = cursor.fetchone()[0]
    
    # Count builder program agents
    cursor.execute("SELECT COUNT(*) FROM agents WHERE builder_grant_program = 1")
    total_builder_agents = cursor.fetchone()[0]
    
    # Count paid builder program agents
    cursor.execute("SELECT COUNT(*) FROM agents WHERE price > 0 AND builder_grant_program = 1")
    paid_builder_agents = cursor.fetchone()[0]
    
    # Count paid NON-builder program agents (the main question)
    cursor.execute("SELECT COUNT(*) FROM agents WHERE price > 0 AND (builder_grant_program = 0 OR builder_grant_program IS NULL)")
    paid_non_builder_agents = cursor.fetchone()[0]
    
    # Count free builder program agents
    cursor.execute("SELECT COUNT(*) FROM agents WHERE (price IS NULL OR price = 0) AND builder_grant_program = 1")
    free_builder_agents = cursor.fetchone()[0]
    
    # Get some examples of paid non-builder agents
    cursor.execute("""
        SELECT agent_id, agent_id_human, name, price, status, executions, reviews_count 
        FROM agents 
        WHERE price > 0 AND (builder_grant_program = 0 OR builder_grant_program IS NULL)
        ORDER BY price DESC
        LIMIT 10
    """)
    examples = cursor.fetchall()
    
    conn.close()
    
    # Display results
    print(f"📊 ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(f"Total agents in database: {total_agents:,}")
    print(f"Total paid agents (price > 0): {total_paid_agents:,}")
    print(f"Total free agents (price = 0 or NULL): {total_free_agents:,}")
    print(f"Total builder program agents: {total_builder_agents:,}")
    print()
    print(f"🎯 MAIN ANSWER:")
    print(f"Paid agents NOT in builder program: {paid_non_builder_agents:,}")
    print()
    print(f"📈 BREAKDOWN:")
    print(f"├── Paid builder program agents: {paid_builder_agents:,}")
    print(f"├── Paid non-builder program agents: {paid_non_builder_agents:,}")
    print(f"└── Free builder program agents: {free_builder_agents:,}")
    print()
    
    # Calculate percentages
    if total_paid_agents > 0:
        pct_paid_non_builder = (paid_non_builder_agents / total_paid_agents) * 100
        pct_paid_builder = (paid_builder_agents / total_paid_agents) * 100
        print(f"💹 PERCENTAGES OF PAID AGENTS:")
        print(f"├── {pct_paid_non_builder:.1f}% are NOT in builder program")
        print(f"└── {pct_paid_builder:.1f}% are in builder program")
        print()
    
    # Show examples
    if examples:
        print(f"💰 TOP 10 PAID NON-BUILDER AGENTS (by price):")
        print(f"{'Agent ID':<12} {'Name':<30} {'Price':<8} {'Status':<8} {'Executions':<12} {'Reviews'}")
        print("-" * 85)
        for example in examples:
            agent_id = example[1] or example[0]  # Use human_id if available, else agent_id
            name = (example[2] or "No name")[:29]  # Truncate long names
            price = f"${example[3]:.2f}" if example[3] else "$0.00"
            status = example[4] or "unknown"
            executions = example[5] or 0
            reviews = example[6] or 0
            print(f"{agent_id:<12} {name:<30} {price:<8} {status:<8} {executions:<12} {reviews}")

def main():
    analyze_paid_non_builder_agents()

if __name__ == "__main__":
    main() 