#!/usr/bin/env python3
"""
Grant Program Builders Agent Analysis

PURPOSE:
This script analyzes all contacts from the Grant Program Builders (HubSpot list 301), 
finds all agents they've built, and creates a comprehensive dataset for comparison 
analysis against other agent groups.

WHAT IT DOES:
1. Gets all contacts from Grant Program Builders (HubSpot list 301) 
2. For each contact, finds all agents they've authored
3. Filters out private agents with < 5 executions
4. Calculates reviews metrics and runs:executions ratio
5. Adds "builder_grant_program" column to database for Grant Program Builder agents
6. Exports results to CSV for further analysis

OUTPUT:
- Summary of total contacts and agents found (filtered)
- CSV file with all agent details including reviews metrics
- Agent IDs for use in comparison analysis
- Database updated with builder_grant_program flag
"""

import os
import sys
import sqlite3
import json
import pandas as pd
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
HUB_API_KEY = os.getenv('HUB_API_KEY')

def add_builder_grant_program_column():
    """Add builder_grant_program column to agents table if it doesn't exist."""
    db_path = 'data/agents.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(agents)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'builder_grant_program' not in columns:
        print("📊 Adding builder_grant_program column to agents table...")
        cursor.execute("ALTER TABLE agents ADD COLUMN builder_grant_program INTEGER DEFAULT 0")
        conn.commit()
        print("✅ Column added successfully")
    else:
        print("📊 builder_grant_program column already exists")
    
    conn.close()

def mark_grant_program_agents(agent_ids):
    """Mark Grant Program Builder agents in the database with builder_grant_program = 1."""
    db_path = 'data/agents.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"🏷️  Marking {len(agent_ids)} Grant Program Builder agents in database...")
    
    # First reset all to 0
    cursor.execute("UPDATE agents SET builder_grant_program = 0")
    
    # Mark Grant Program Builder agents as 1
    for agent_id in agent_ids:
        cursor.execute("UPDATE agents SET builder_grant_program = 1 WHERE agent_id = ?", (agent_id,))
    
    conn.commit()
    conn.close()
    print("✅ Grant Program Builder agents marked successfully")

def fetch_grant_program_contacts():
    """Fetch all contacts from Grant Program Builders (HubSpot list 301)."""
    if not HUB_API_KEY:
        print("Error: HUB_API_KEY not set in .env file.")
        sys.exit(1)
    
    list_id = 301
    url = f"https://api.hubapi.com/contacts/v1/lists/{list_id}/contacts/all"
    headers = {
        "Authorization": f"Bearer {HUB_API_KEY}",
        "Content-Type": "application/json"
    }
    
    all_contacts = []
    vid_offset = None
    
    while True:
        params = {
            "count": 100,
            "property": ["email", "platform_user_token"]
        }
        
        if vid_offset:
            params["vidOffset"] = vid_offset
            
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"Error: Status code {response.status_code}")
                print(response.text)
                sys.exit(1)
                
            data = response.json()
            contacts = data.get('contacts', [])
            
            if not contacts:
                break
                
            # Process each contact
            for contact in contacts:
                properties = contact.get('properties', {})
                
                # Extract email and platform_user_token
                email_prop = properties.get('email', {})
                email = email_prop.get('value') if email_prop else None
                
                token_prop = properties.get('platform_user_token', {})
                platform_user_token = token_prop.get('value') if token_prop else None
                
                # Only include contacts that have both email and platform_user_token
                if email and platform_user_token:
                    all_contacts.append({
                        'email': email,
                        'platform_user_token': platform_user_token
                    })
            
            # Check for pagination
            has_more = data.get('has-more', False)
            vid_offset = data.get('vid-offset')
            
            if not has_more or not vid_offset:
                break
                
        except Exception as e:
            print(f"Error fetching contacts from Grant Program Builder list: {e}")
            sys.exit(1)
    
    return all_contacts

def get_user_agents_detailed(user_token, db_path=None):
    """Get all agents authored by a specific user token with full details."""
    # Determine the correct database path
    if db_path is None:
        db_path = 'data/agents.db'
        if not os.path.exists(db_path):
            print("Error: Cannot find agents.db database")
            return []
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query to find all agents where the user_token is a key in the authors JSON
    query = """
    SELECT agent_id, agent_id_human, name, description, status, created_at, 
           executions, reviews_count, reviews_score, price, tags, type
    FROM agents
    WHERE EXISTS (
        SELECT 1 FROM json_each(authors) 
        WHERE json_each.key = ?
    )
    ORDER BY created_at DESC
    """
    
    cursor.execute(query, (user_token,))
    results = cursor.fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    agents = []
    for row in results:
        executions = row[6] or 0
        reviews_count = row[7] or 0
        reviews_score = row[8] or 0
        
        # Calculate runs:executions ratio (assuming runs = executions for now)
        runs_executions_ratio = 1.0 if executions > 0 else 0.0
        
        # Calculate average rating (reviews_score is already the average)
        average_rating = reviews_score if reviews_count > 0 else 0.0
        
        agent_data = {
            'agent_id': row[0],
            'agent_id_human': row[1], 
            'name': row[2],
            'description': row[3],
            'status': row[4],
            'created_at': row[5],
            'executions': executions,
            'reviews_count': reviews_count,
            'reviews_score': reviews_score,
            'price': row[9],
            'tags': row[10],
            'type': row[11],
            'author_email': None,  # Will be filled in
            'author_user_token': user_token,
            'runs_executions_ratio': runs_executions_ratio,
            'average_rating': average_rating
        }
        
        # Filter: Remove private agents with < 5 executions
        if row[4] == 'private' and executions < 5:
            continue  # Skip this agent
            
        agents.append(agent_data)
    
    return agents

def main():
    print("🔍 Analyzing Grant Program Builders and Their Agents")
    print("=" * 60)
    
    # Step 0: Add builder_grant_program column if needed
    add_builder_grant_program_column()
    
    # Step 1: Get Grant Program Builder contacts
    print("\n📋 Fetching Grant Program Builder contacts...")
    contacts = fetch_grant_program_contacts()
    print(f"Found {len(contacts)} Grant Program Builders with both email and platform_user_token")
    
    # Step 2: For each contact, get all their agents
    all_agents = []
    contact_summary = []
    filtered_out_count = 0
    
    for i, contact in enumerate(contacts, 1):
        email = contact['email']
        user_token = contact['platform_user_token']
        
        print(f"\n[{i}/{len(contacts)}] Analyzing {email} ({user_token})")
        
        # Get all agents (before filtering)
        db_path = 'data/agents.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM agents
            WHERE EXISTS (
                SELECT 1 FROM json_each(authors) 
                WHERE json_each.key = ?
            )
        """, (user_token,))
        total_before_filter = cursor.fetchone()[0]
        
        # Count private agents with < 5 executions
        cursor.execute("""
            SELECT COUNT(*) FROM agents
            WHERE EXISTS (
                SELECT 1 FROM json_each(authors) 
                WHERE json_each.key = ?
            ) AND status = 'private' AND (executions IS NULL OR executions < 5)
        """, (user_token,))
        private_low_exec = cursor.fetchone()[0]
        conn.close()
        
        filtered_out_count += private_low_exec
        
        agents = get_user_agents_detailed(user_token)
        
        # Add email to each agent record
        for agent in agents:
            agent['author_email'] = email
        
        all_agents.extend(agents)
        
        contact_summary.append({
            'email': email,
            'user_token': user_token,
            'total_agents_before_filter': total_before_filter,
            'filtered_out_private_low_exec': private_low_exec,
            'total_agents': len(agents),
            'public_agents': len([a for a in agents if a['status'] == 'public']),
            'private_agents': len([a for a in agents if a['status'] == 'private']),
            'total_executions': sum(a['executions'] or 0 for a in agents),
            'total_reviews': sum(a['reviews_count'] or 0 for a in agents),
            'avg_rating': sum(a['average_rating'] * (a['reviews_count'] or 0) for a in agents) / max(sum(a['reviews_count'] or 0 for a in agents), 1)
        })
        
        print(f"   Found {len(agents)} agents after filtering ({total_before_filter} before, {private_low_exec} filtered out)")
        print(f"   ({len([a for a in agents if a['status'] == 'public'])} public, {len([a for a in agents if a['status'] == 'private'])} private)")
    
    # Step 3: Mark agents in database
    agent_ids = [agent['agent_id'] for agent in all_agents]
    mark_grant_program_agents(agent_ids)
    
    # Step 4: Generate summary
    print(f"\n{'='*60}")
    print("📊 GRANT PROGRAM BUILDERS ANALYSIS SUMMARY")
    print(f"{'='*60}")
    print(f"Total Grant Program Builders: {len(contacts)}")
    print(f"Total agents found (after filtering): {len(all_agents)}")
    print(f"Private agents with < 5 executions filtered out: {filtered_out_count}")
    print(f"Public agents: {len([a for a in all_agents if a['status'] == 'public'])}")
    print(f"Private agents (≥5 executions): {len([a for a in all_agents if a['status'] == 'private'])}")
    print(f"Total executions: {sum(a['executions'] or 0 for a in all_agents):,}")
    print(f"Total reviews: {sum(a['reviews_count'] or 0 for a in all_agents):,}")
    
    # Calculate overall average rating
    total_weighted_rating = sum(a['average_rating'] * (a['reviews_count'] or 0) for a in all_agents)
    total_reviews = sum(a['reviews_count'] or 0 for a in all_agents)
    overall_avg_rating = total_weighted_rating / max(total_reviews, 1)
    print(f"Overall average rating: {overall_avg_rating:.2f}")
    
    # Step 5: Export to CSV files
    print(f"\n📁 Exporting data...")
    
    # Determine output directory based on current working directory
    output_dir = 'data'
    
    # Export all agents
    agents_df = pd.DataFrame(all_agents)
    agents_output = os.path.join(output_dir, 'grant_program_builders_agents.csv')
    agents_df.to_csv(agents_output, index=False)
    print(f"✅ All agents exported to: {agents_output}")
    
    # Export contact summary
    summary_df = pd.DataFrame(contact_summary)
    summary_output = os.path.join(output_dir, 'grant_program_builders_summary.csv')
    summary_df.to_csv(summary_output, index=False)
    print(f"✅ Contact summary exported to: {summary_output}")
    
    # Export just agent IDs for easy reference
    agent_ids_df = pd.DataFrame({'agent_id': agent_ids})
    ids_output = os.path.join(output_dir, 'grant_program_builders_agent_ids.csv')
    agent_ids_df.to_csv(ids_output, index=False)
    print(f"✅ Agent IDs exported to: {ids_output}")
    
    print(f"\n🎯 Ready for comparison analysis!")
    print(f"Grant Program Builder agent IDs available in: {ids_output}")
    print(f"🏷️  Grant Program Builder agents marked in database with builder_grant_program = 1")

if __name__ == "__main__":
    main() 