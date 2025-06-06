#!/usr/bin/env python3
"""
User Agent Builds Analyzer

PURPOSE:
This script generates a detailed briefing of all agents authored by a specific user.
It queries the local agents database and shows comprehensive information about each
agent created by the specified user token.

USAGE:
Show all agents by a user:
    python user_builds.py -u <user_token>

Filter by status:
    python user_builds.py -u <user_token> -p public
    python user_builds.py -u <user_token> -p private

WHAT IT SHOWS:
For each agent authored by the user:
- Agent name
- Human-readable ID  
- Internal agent ID
- Creation date
- Number of executions/runs

REQUIREMENTS:
- Local agents.db database with agents table
- User tokens stored in JSON format in the 'authors' field

OUTPUT:
Formatted briefing showing:
- Total count of agents authored
- Detailed list of each agent with metadata
- Sorted by creation date (newest first)

This is useful for analyzing user productivity and understanding what agents
specific users have built on the platform.
"""

import sqlite3
import argparse
import sys

def get_user_agents(user_token, status=None, db_path='data/agents.db'):
    """Get all agents authored by a specific user token."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query to find all agents where the user_token is a key in the authors JSON
    base_query = """
    SELECT name, agent_id_human, agent_id, created_at, executions
    FROM agents
    WHERE EXISTS (
        SELECT 1 FROM json_each(authors) 
        WHERE json_each.key = ?
    )
    """
    
    # Add status filter if provided
    if status:
        query = base_query + " AND status = ? ORDER BY created_at DESC;"
        cursor.execute(query, (user_token, status))
    else:
        query = base_query + " ORDER BY created_at DESC;"
        cursor.execute(query, (user_token,))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def print_user_briefing(user_token, agents, status=None):
    """Print a formatted briefing for the user's agents."""
    status_text = f" ({status.upper()})" if status else ""
    print(f"\n=== USER BRIEFING FOR TOKEN: {user_token}{status_text} ===")
    print(f"Total agents authored: {len(agents)}")
    print("=" * 80)
    
    if not agents:
        print("No agents found for this user token.")
        return
    
    for i, (name, agent_id_human, agent_id, created_at, executions) in enumerate(agents, 1):
        print(f"\n{i}. {name}")
        print(f"   Human ID: {agent_id_human}")
        print(f"   Agent ID: {agent_id}")
        print(f"   Created:  {created_at}")
        print(f"   Runs:     {executions}")
        print("-" * 60)

def main():
    parser = argparse.ArgumentParser(description='Generate a briefing of agents built by a specific user.')
    parser.add_argument('-u', '--user_token', required=True, help='The user_token to look up')
    parser.add_argument('-p', '--status', choices=['public', 'private'], help='Filter by agent status (public or private). If not provided, shows both.')
    args = parser.parse_args()
    
    try:
        agents = get_user_agents(args.user_token, args.status)
        print_user_briefing(args.user_token, agents, args.status)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 