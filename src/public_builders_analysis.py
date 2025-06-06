#!/usr/bin/env python3
"""
Group B Builders Analysis

PURPOSE:
This script analyzes Group B builders - unique builders who have created public agents,
excluding the Grant Program Builders, to understand the broader ecosystem.

WHAT IT DOES:
1. Finds all public agents in the database
2. Excludes Grant Program Builder agents (builder_grant_program = 1)
3. Extracts unique user_tokens from public agent authors (Group B)
4. Compares Group B against Grant Program Builders
5. Provides comprehensive Group B builder statistics

OUTPUT:
- Count of unique Group B builders (public agent creators excluding Grant Program Builders)
- Comparison statistics between Grant Program Builders and Group B
- Top Group B builders by public agent count
"""

import sqlite3
import json
import pandas as pd
from collections import defaultdict

def analyze_group_b_builders():
    """Analyze Group B builders - unique builders of public agents, excluding Grant Program Builders."""
    
    db_path = 'data/agents.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Analyzing Group B Builders (Public Agent Creators Excluding Grant Program Builders)")
    print("=" * 80)
    
    # Step 1: Get all public agents excluding Grant Program Builder agents
    print("\n📊 Querying Group B public agents...")
    cursor.execute("""
        SELECT agent_id, authors, executions, reviews_count, reviews_score
        FROM agents 
        WHERE status = 'public' 
        AND (builder_grant_program IS NULL OR builder_grant_program != 1)
    """)
    
    public_agents = cursor.fetchall()
    print(f"Found {len(public_agents)} Group B public agents")
    
    # Step 2: Extract unique user tokens from authors
    print("\n👤 Extracting unique Group B builders...")
    builder_stats = defaultdict(lambda: {
        'agent_count': 0,
        'total_executions': 0,
        'total_reviews': 0,
        'total_weighted_rating': 0,
        'agent_ids': []
    })
    
    group_b_builders = set()
    
    for agent_id, authors_json, executions, reviews_count, reviews_score in public_agents:
        if authors_json:
            try:
                authors = json.loads(authors_json)
                for user_token in authors.keys():
                    group_b_builders.add(user_token)
                    builder_stats[user_token]['agent_count'] += 1
                    builder_stats[user_token]['total_executions'] += executions or 0
                    builder_stats[user_token]['total_reviews'] += reviews_count or 0
                    if reviews_count and reviews_count > 0:
                        builder_stats[user_token]['total_weighted_rating'] += (reviews_score or 0) * reviews_count
                    builder_stats[user_token]['agent_ids'].append(agent_id)
            except json.JSONDecodeError:
                continue
    
    print(f"Found {len(group_b_builders)} unique Group B builders")
    
    # Step 3: Get Grant Program Builder statistics for comparison
    print("\n📈 Getting Grant Program Builder statistics for comparison...")
    cursor.execute("""
        SELECT COUNT(DISTINCT agent_id) as total_public_agents,
               COUNT(DISTINCT CASE WHEN builder_grant_program = 1 THEN agent_id END) as grant_program_public_agents
        FROM agents 
        WHERE status = 'public'
    """)
    
    total_public, grant_program_public = cursor.fetchone()
    
    # Get unique Grant Program Builders who have public agents
    cursor.execute("""
        SELECT authors
        FROM agents 
        WHERE status = 'public' 
        AND builder_grant_program = 1
    """)
    
    grant_program_authors = cursor.fetchall()
    grant_program_builders = set()
    
    for (authors_json,) in grant_program_authors:
        if authors_json:
            try:
                authors = json.loads(authors_json)
                grant_program_builders.update(authors.keys())
            except json.JSONDecodeError:
                continue
    
    conn.close()
    
    # Step 4: Calculate and display results
    print(f"\n{'='*80}")
    print("📊 GROUP B BUILDERS ANALYSIS RESULTS")
    print(f"{'='*80}")
    print(f"Total public agents on platform: {total_public:,}")
    print(f"Public agents by Grant Program Builders: {grant_program_public:,}")
    print(f"Public agents by Group B builders: {len(public_agents):,}")
    print()
    print(f"Grant Program Builders with public agents: {len(grant_program_builders)}")
    print(f"Group B builders with public agents: {len(group_b_builders)}")
    print(f"Total unique builders with public agents: {len(grant_program_builders) + len(group_b_builders)}")
    
    # Calculate percentages
    grant_program_percentage = (grant_program_public / total_public) * 100 if total_public > 0 else 0
    group_b_percentage = (len(public_agents) / total_public) * 100 if total_public > 0 else 0
    
    print(f"\nPercentage breakdown:")
    print(f"Grant Program Builders: {grant_program_percentage:.1f}% of public agents")
    print(f"Group B builders: {group_b_percentage:.1f}% of public agents")
    
    # Calculate productivity metrics
    grant_avg_agents = grant_program_public / len(grant_program_builders) if len(grant_program_builders) > 0 else 0
    group_b_avg_agents = len(public_agents) / len(group_b_builders) if len(group_b_builders) > 0 else 0
    
    print(f"\nProductivity comparison:")
    print(f"Grant Program Builders: {grant_avg_agents:.1f} public agents per builder")
    print(f"Group B builders: {group_b_avg_agents:.1f} public agents per builder")
    
    # Step 5: Top Group B builders analysis
    print(f"\n🏆 TOP 10 GROUP B BUILDERS:")
    print("-" * 80)
    
    # Sort builders by agent count
    sorted_builders = sorted(builder_stats.items(), key=lambda x: x[1]['agent_count'], reverse=True)
    
    print(f"{'Rank':<5} {'User Token':<35} {'Agents':<8} {'Executions':<12} {'Avg Rating':<10}")
    print("-" * 80)
    
    for i, (user_token, stats) in enumerate(sorted_builders[:10], 1):
        avg_rating = (stats['total_weighted_rating'] / stats['total_reviews']) if stats['total_reviews'] > 0 else 0
        print(f"{i:<5} {user_token:<35} {stats['agent_count']:<8} {stats['total_executions']:<12,} {avg_rating:<10.2f}")
    
    # Step 6: Export Group B summary
    print(f"\n📁 Exporting Group B data...")
    
    summary_data = []
    for user_token, stats in sorted_builders:
        avg_rating = (stats['total_weighted_rating'] / stats['total_reviews']) if stats['total_reviews'] > 0 else 0
        summary_data.append({
            'user_token': user_token,
            'public_agent_count': stats['agent_count'],
            'total_executions': stats['total_executions'],
            'total_reviews': stats['total_reviews'],
            'average_rating': avg_rating
        })
    
    # Export to CSV
    df = pd.DataFrame(summary_data)
    output_file = 'group_b_builders_summary.csv'
    df.to_csv(output_file, index=False)
    print(f"✅ Group B builders exported to: {output_file}")
    
    # Export Group B builder IDs for easy reference
    group_b_ids = list(group_b_builders)
    ids_df = pd.DataFrame({'user_token': group_b_ids})
    ids_output = 'group_b_builders_user_tokens.csv'
    ids_df.to_csv(ids_output, index=False)
    print(f"✅ Group B builder user tokens exported to: {ids_output}")
    
    return {
        'group_b_builders': len(group_b_builders),
        'grant_program_builders': len(grant_program_builders),
        'total_public_agents': total_public,
        'grant_program_public_agents': grant_program_public,
        'group_b_public_agents': len(public_agents)
    }

if __name__ == "__main__":
    results = analyze_group_b_builders()
    
    print(f"\n🎯 BUILDER GROUPS SUMMARY:")
    print(f"   Grant Program Builders with public agents: {results['grant_program_builders']}")
    print(f"   Group B builders with public agents: {results['group_b_builders']}")
    print(f"   Total builders with public agents: {results['group_b_builders'] + results['grant_program_builders']}")
    print(f"\n📊 Two distinct builder groups now defined for analysis!") 