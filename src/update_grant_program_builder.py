#!/usr/bin/env python3
"""
Update Grant Program Builder Status

PURPOSE:
Updates the builder_grant_program status for agents authored by a specific user.

USAGE:
python update_grant_program_builder.py -u <user_token> [-a <agent_id>]

EXAMPLES:
python update_grant_program_builder.py -u 94dfb55e751c4d35b485872a31d63e33
python update_grant_program_builder.py -u 94dfb55e751c4d35b485872a31d63e33 -a lt8gzzc4s59qym06
"""

import sqlite3
import json
import argparse

def check_and_update_builder(user_token, target_agent_id=None):
    """Check and update grant program builder status for a user."""
    
    db_path = 'data/agents.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"🔍 Searching for agents by user: {user_token}")
    
    # First, let's check if the target agent exists and its current status
    if target_agent_id:
        cursor.execute("SELECT agent_id, name, authors, builder_grant_program FROM agents WHERE agent_id = ?", (target_agent_id,))
        result = cursor.fetchone()
        if result:
            agent_id, name, authors_json, builder_status = result
            print(f"\n📋 Target agent found:")
            print(f"   Agent ID: {agent_id}")
            print(f"   Name: {name}")
            print(f"   Builder Grant Program: {builder_status}")
            
            if authors_json:
                try:
                    authors = json.loads(authors_json)
                    print(f"   Authors: {list(authors.keys())}")
                    
                    if user_token in authors:
                        print(f"✅ User {user_token} is indeed an author of this agent")
                    else:
                        print(f"❌ User {user_token} is NOT an author of this agent")
                        print(f"   Current authors: {list(authors.keys())}")
                except json.JSONDecodeError:
                    print(f"   Authors JSON parsing failed: {authors_json}")
            else:
                print(f"   No authors data")
        else:
            print(f"❌ Target agent {target_agent_id} not found")
    
    # Find all agents by this user
    cursor.execute("SELECT agent_id, name, status, authors, builder_grant_program FROM agents")
    all_agents = cursor.fetchall()
    
    user_agents = []
    
    for agent_id, name, status, authors_json, builder_status in all_agents:
        if authors_json:
            try:
                authors = json.loads(authors_json)
                if user_token in authors:
                    user_agents.append({
                        'agent_id': agent_id,
                        'name': name,
                        'status': status,
                        'builder_grant_program': builder_status
                    })
            except json.JSONDecodeError:
                continue
    
    print(f"\n📊 Found {len(user_agents)} agents by user {user_token}:")
    
    if not user_agents:
        print("❌ No agents found for this user")
        conn.close()
        return
    
    for agent in user_agents:
        print(f"   {agent['agent_id']} - {agent['name']} ({agent['status']}) - Grant Program: {agent['builder_grant_program']}")
    
    # Update all agents by this user to be Grant Program Builder agents
    print(f"\n🔄 Updating all agents by {user_token} to Grant Program Builder status...")
    
    for agent in user_agents:
        cursor.execute(
            "UPDATE agents SET builder_grant_program = 1 WHERE agent_id = ?",
            (agent['agent_id'],)
        )
        print(f"✅ Updated {agent['agent_id']} - {agent['name']}")
    
    conn.commit()
    conn.close()
    
    print(f"\n🎯 Successfully updated {len(user_agents)} agents for Grant Program Builder: {user_token}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update Grant Program Builder status for agents by user token')
    parser.add_argument('-u', '--user_token', required=True, help='The user token to update')
    parser.add_argument('-a', '--agent_id', help='Optional specific agent ID to check')
    
    args = parser.parse_args()
    
    check_and_update_builder(args.user_token, args.agent_id) 