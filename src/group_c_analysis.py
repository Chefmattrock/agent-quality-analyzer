#!/usr/bin/env python3
"""
Group C Analysis

PURPOSE:
This script analyzes Group C - all public agents excluding those that receive paid traffic.
This represents the "organic" public agent ecosystem.

WHAT IT DOES:
1. Loads the paid traffic exclusion list (agents that receive paid traffic)
2. Finds all public agents excluding the paid traffic agents
3. Extracts unique builders in Group C
4. Provides comprehensive Group C statistics and analysis
5. Compares Group C against Grant Program Builders and Group B

OUTPUT:
- Count of Group C agents and builders
- Comparison with other groups
- Top Group C builders analysis
- Export files for further analysis
"""

import sqlite3
import json
import pandas as pd
from collections import defaultdict

def load_exclusion_list():
    """Load the paid traffic agents exclusion list."""
    try:
        df = pd.read_csv('paid_traffic_exclusion_list.csv')
        return set(df['agent_id'].tolist())
    except FileNotFoundError:
        print("❌ Exclusion list not found. Please run find_paid_traffic_agents.py first.")
        return set()

def analyze_group_c():
    """Analyze Group C - public agents excluding paid traffic agents."""
    
    # Load exclusion list
    print("📋 Loading paid traffic exclusion list...")
    exclusion_list = load_exclusion_list()
    
    if not exclusion_list:
        return None
    
    print(f"Found {len(exclusion_list)} agents to exclude from Group C")
    
    db_path = 'data/agents.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 Analyzing Group C (Public Agents Excluding Paid Traffic)")
    print("=" * 80)
    
    # Step 1: Get all public agents
    print("\n📊 Querying all public agents...")
    cursor.execute("""
        SELECT agent_id, authors, executions, reviews_count, reviews_score, name
        FROM agents 
        WHERE status = 'public'
    """)
    
    all_public_agents = cursor.fetchall()
    print(f"Found {len(all_public_agents)} total public agents")
    
    # Step 2: Filter out paid traffic agents and Grant Program Builder agents
    print(f"\n🚫 Filtering out paid traffic agents and Grant Program Builder agents...")
    
    group_c_agents = []
    excluded_paid_traffic = 0
    excluded_grant_program = 0
    
    for agent_id, authors_json, executions, reviews_count, reviews_score, name in all_public_agents:
        # Exclude paid traffic agents
        if agent_id in exclusion_list:
            excluded_paid_traffic += 1
            continue
        
        # Check if it's a Grant Program Builder agent
        cursor.execute("SELECT builder_grant_program FROM agents WHERE agent_id = ?", (agent_id,))
        result = cursor.fetchone()
        if result and result[0] == 1:
            excluded_grant_program += 1
            continue
        
        # This is a Group C agent
        group_c_agents.append((agent_id, authors_json, executions, reviews_count, reviews_score, name))
    
    print(f"Excluded {excluded_paid_traffic} paid traffic agents")
    print(f"Excluded {excluded_grant_program} Grant Program Builder agents")
    print(f"Group C agents: {len(group_c_agents)}")
    
    # Step 3: Extract unique Group C builders and their statistics
    print(f"\n👤 Extracting unique Group C builders...")
    
    builder_stats = defaultdict(lambda: {
        'agent_count': 0,
        'total_executions': 0,
        'total_reviews': 0,
        'total_weighted_rating': 0,
        'agent_ids': [],
        'agent_names': []
    })
    
    group_c_builders = set()
    total_executions = 0
    total_reviews = 0
    total_weighted_rating = 0
    
    for agent_id, authors_json, executions, reviews_count, reviews_score, name in group_c_agents:
        total_executions += executions or 0
        total_reviews += reviews_count or 0
        if reviews_count and reviews_count > 0:
            total_weighted_rating += (reviews_score or 0) * reviews_count
        
        if authors_json:
            try:
                authors = json.loads(authors_json)
                for user_token in authors.keys():
                    group_c_builders.add(user_token)
                    builder_stats[user_token]['agent_count'] += 1
                    builder_stats[user_token]['total_executions'] += executions or 0
                    builder_stats[user_token]['total_reviews'] += reviews_count or 0
                    if reviews_count and reviews_count > 0:
                        builder_stats[user_token]['total_weighted_rating'] += (reviews_score or 0) * reviews_count
                    builder_stats[user_token]['agent_ids'].append(agent_id)
                    builder_stats[user_token]['agent_names'].append(name or 'Unnamed')
            except json.JSONDecodeError:
                continue
    
    print(f"Found {len(group_c_builders)} unique Group C builders")
    
    # Step 4: Get comparison data
    print(f"\n📈 Getting comparison data...")
    
    # Total public agents
    cursor.execute("SELECT COUNT(*) FROM agents WHERE status = 'public'")
    total_public_agents = cursor.fetchone()[0]
    
    # Grant Program Builder public agents
    cursor.execute("SELECT COUNT(*) FROM agents WHERE status = 'public' AND builder_grant_program = 1")
    grant_program_public_agents = cursor.fetchone()[0]
    
    # Group B public agents (excluding Grant Program Builders and paid traffic)
    group_b_count = total_public_agents - grant_program_public_agents - excluded_paid_traffic
    
    # Grant Program Builder count
    cursor.execute("SELECT authors FROM agents WHERE status = 'public' AND builder_grant_program = 1")
    grant_authors = cursor.fetchall()
    grant_program_builders = set()
    for (authors_json,) in grant_authors:
        if authors_json:
            try:
                authors = json.loads(authors_json)
                grant_program_builders.update(authors.keys())
            except json.JSONDecodeError:
                continue
    
    # Group B builders (need to calculate from remaining agents)
    cursor.execute("""
        SELECT authors FROM agents 
        WHERE status = 'public' 
        AND (builder_grant_program IS NULL OR builder_grant_program != 1)
    """)
    
    group_b_authors = cursor.fetchall()
    group_b_builders = set()
    
    for (authors_json,) in group_b_authors:
        if authors_json:
            try:
                authors = json.loads(authors_json)
                for user_token in authors.keys():
                    # Check if this agent is not in paid traffic exclusion list
                    cursor.execute("SELECT agent_id FROM agents WHERE authors LIKE ? AND status = 'public'", 
                                 (f'%{user_token}%',))
                    user_agents = cursor.fetchall()
                    
                    has_non_excluded_agent = False
                    for (agent_id,) in user_agents:
                        if agent_id not in exclusion_list:
                            has_non_excluded_agent = True
                            break
                    
                    if has_non_excluded_agent:
                        group_b_builders.add(user_token)
            except json.JSONDecodeError:
                continue
    
    conn.close()
    
    # Step 5: Calculate and display results
    print(f"\n{'='*80}")
    print("📊 GROUP C ANALYSIS RESULTS")
    print(f"{'='*80}")
    
    print(f"AGENT BREAKDOWN:")
    print(f"Total public agents on platform: {total_public_agents:,}")
    print(f"├─ Grant Program Builder agents: {grant_program_public_agents:,}")
    print(f"├─ Paid traffic agents: {excluded_paid_traffic:,}")
    print(f"└─ Group C agents (organic public): {len(group_c_agents):,}")
    
    print(f"\nBUILDER BREAKDOWN:")
    print(f"├─ Grant Program Builders: {len(grant_program_builders):,}")
    print(f"├─ Group B builders (public, non-Grant Program): {len(group_b_builders):,}")
    print(f"└─ Group C builders (organic public): {len(group_c_builders):,}")
    
    # Calculate percentages
    group_c_percentage = (len(group_c_agents) / total_public_agents) * 100 if total_public_agents > 0 else 0
    
    print(f"\nGROUP C STATISTICS:")
    print(f"Agents: {len(group_c_agents):,} ({group_c_percentage:.1f}% of all public agents)")
    print(f"Builders: {len(group_c_builders):,}")
    print(f"Total executions: {total_executions:,}")
    print(f"Total reviews: {total_reviews:,}")
    
    avg_rating = (total_weighted_rating / total_reviews) if total_reviews > 0 else 0
    avg_agents_per_builder = len(group_c_agents) / len(group_c_builders) if len(group_c_builders) > 0 else 0
    
    print(f"Average rating: {avg_rating:.2f}⭐")
    print(f"Average agents per builder: {avg_agents_per_builder:.1f}")
    
    # Step 6: Top Group C builders analysis
    print(f"\n🏆 TOP 15 GROUP C BUILDERS:")
    print("-" * 90)
    
    # Sort builders by agent count
    sorted_builders = sorted(builder_stats.items(), key=lambda x: x[1]['agent_count'], reverse=True)
    
    print(f"{'Rank':<5} {'User Token':<35} {'Agents':<8} {'Executions':<12} {'Avg Rating':<10}")
    print("-" * 90)
    
    for i, (user_token, stats) in enumerate(sorted_builders[:15], 1):
        avg_rating = (stats['total_weighted_rating'] / stats['total_reviews']) if stats['total_reviews'] > 0 else 0
        print(f"{i:<5} {user_token:<35} {stats['agent_count']:<8} {stats['total_executions']:<12,} {avg_rating:<10.2f}")
    
    # Step 7: Export Group C data
    print(f"\n📁 Exporting Group C data...")
    
    # Detailed builder summary
    summary_data = []
    for user_token, stats in sorted_builders:
        avg_rating = (stats['total_weighted_rating'] / stats['total_reviews']) if stats['total_reviews'] > 0 else 0
        summary_data.append({
            'user_token': user_token,
            'public_agent_count': stats['agent_count'],
            'total_executions': stats['total_executions'],
            'total_reviews': stats['total_reviews'],
            'average_rating': avg_rating,
            'top_agents': ', '.join(stats['agent_names'][:3])  # Top 3 agent names
        })
    
    # Export to CSV
    df = pd.DataFrame(summary_data)
    output_file = 'group_c_builders_summary.csv'
    df.to_csv(output_file, index=False)
    print(f"✅ Group C builders exported to: {output_file}")
    
    # Export Group C builder IDs
    group_c_ids = list(group_c_builders)
    ids_df = pd.DataFrame({'user_token': group_c_ids})
    ids_output = 'group_c_builders_user_tokens.csv'
    ids_df.to_csv(ids_output, index=False)
    print(f"✅ Group C builder user tokens exported to: {ids_output}")
    
    # Export Group C agent details
    agent_details = []
    for agent_id, authors_json, executions, reviews_count, reviews_score, name in group_c_agents:
        avg_rating = (reviews_score or 0) if reviews_count and reviews_count > 0 else 0
        agent_details.append({
            'agent_id': agent_id,
            'name': name or 'Unnamed',
            'executions': executions or 0,
            'reviews_count': reviews_count or 0,
            'average_rating': avg_rating
        })
    
    agents_df = pd.DataFrame(agent_details)
    agents_output = 'group_c_agents.csv'
    agents_df.to_csv(agents_output, index=False)
    print(f"✅ Group C agents exported to: {agents_output}")
    
    return {
        'group_c_builders': len(group_c_builders),
        'group_c_agents': len(group_c_agents),
        'total_public_agents': total_public_agents,
        'grant_program_agents': grant_program_public_agents,
        'paid_traffic_agents': excluded_paid_traffic
    }

if __name__ == "__main__":
    results = analyze_group_c()
    
    if results:
        print(f"\n🎯 THREE GROUP ECOSYSTEM SUMMARY:")
        print(f"   Grant Program Builders: {results['grant_program_agents']} agents")
        print(f"   Paid Traffic Agents: {results['paid_traffic_agents']} agents") 
        print(f"   Group C (Organic): {results['group_c_agents']} agents")
        print(f"   ────────────────────────────────────────")
        print(f"   Total Public Agents: {results['total_public_agents']} agents")
        print(f"\n🌱 Group C represents the organic, non-promoted public agent ecosystem!")
    else:
        print("❌ Analysis failed. Please ensure exclusion list exists.") 