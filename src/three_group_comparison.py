#!/usr/bin/env python3
"""
Three Group Comparison Analysis

PURPOSE:
Comprehensive comparison of the three builder/agent groups:
- Group A: Grant Program Builders
- Group B: ALL Public Agents  
- Group C: Organic Public Agents (excluding paid traffic + Grant Program Builder agents)

METRICS:
- Total Agents and % of all public agents
- Average # of Agents per builder
- Total Executions & Average Executions per Agent
- Total Review count & Average reviews per agent & Average review score
- Top 10 Agents and Top 10 Builders for each group
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

def analyze_group_a(cursor):
    """Analyze Group A: Grant Program Builders."""
    print("🅰️ Analyzing Group A: Grant Program Builders...")
    
    # Get Grant Program Builder agents
    cursor.execute("""
        SELECT agent_id, authors, executions, reviews_count, reviews_score, name
        FROM agents 
        WHERE status = 'public' AND builder_grant_program = 1
    """)
    
    agents = cursor.fetchall()
    
    # Extract builders and stats
    builder_stats = defaultdict(lambda: {
        'agent_count': 0, 'total_executions': 0, 'total_reviews': 0, 
        'total_weighted_rating': 0, 'agent_details': []
    })
    
    builders = set()
    total_executions = 0
    total_reviews = 0
    total_weighted_rating = 0
    agent_details = []
    
    for agent_id, authors_json, executions, reviews_count, reviews_score, name in agents:
        exec_count = executions or 0
        review_count = reviews_count or 0
        rating = reviews_score or 0
        
        total_executions += exec_count
        total_reviews += review_count
        if review_count > 0:
            total_weighted_rating += rating * review_count
        
        agent_details.append({
            'agent_id': agent_id,
            'name': name or 'Unnamed',
            'executions': exec_count,
            'reviews_count': review_count,
            'average_rating': rating
        })
        
        if authors_json:
            try:
                authors = json.loads(authors_json)
                for user_token in authors.keys():
                    builders.add(user_token)
                    builder_stats[user_token]['agent_count'] += 1
                    builder_stats[user_token]['total_executions'] += exec_count
                    builder_stats[user_token]['total_reviews'] += review_count
                    if review_count > 0:
                        builder_stats[user_token]['total_weighted_rating'] += rating * review_count
                    builder_stats[user_token]['agent_details'].append({
                        'name': name or 'Unnamed',
                        'executions': exec_count,
                        'rating': rating
                    })
            except json.JSONDecodeError:
                continue
    
    return {
        'agents': agents,
        'agent_count': len(agents),
        'builder_count': len(builders),
        'total_executions': total_executions,
        'total_reviews': total_reviews,
        'total_weighted_rating': total_weighted_rating,
        'builder_stats': builder_stats,
        'agent_details': agent_details
    }

def analyze_group_b(cursor):
    """Analyze Group B: ALL Public Agents."""
    print("🅱️ Analyzing Group B: ALL Public Agents...")
    
    # Get ALL public agents
    cursor.execute("""
        SELECT agent_id, authors, executions, reviews_count, reviews_score, name
        FROM agents 
        WHERE status = 'public'
    """)
    
    agents = cursor.fetchall()
    
    # Extract builders and stats
    builder_stats = defaultdict(lambda: {
        'agent_count': 0, 'total_executions': 0, 'total_reviews': 0, 
        'total_weighted_rating': 0, 'agent_details': []
    })
    
    builders = set()
    total_executions = 0
    total_reviews = 0
    total_weighted_rating = 0
    agent_details = []
    
    for agent_id, authors_json, executions, reviews_count, reviews_score, name in agents:
        exec_count = executions or 0
        review_count = reviews_count or 0
        rating = reviews_score or 0
        
        total_executions += exec_count
        total_reviews += review_count
        if review_count > 0:
            total_weighted_rating += rating * review_count
        
        agent_details.append({
            'agent_id': agent_id,
            'name': name or 'Unnamed',
            'executions': exec_count,
            'reviews_count': review_count,
            'average_rating': rating
        })
        
        if authors_json:
            try:
                authors = json.loads(authors_json)
                for user_token in authors.keys():
                    builders.add(user_token)
                    builder_stats[user_token]['agent_count'] += 1
                    builder_stats[user_token]['total_executions'] += exec_count
                    builder_stats[user_token]['total_reviews'] += review_count
                    if review_count > 0:
                        builder_stats[user_token]['total_weighted_rating'] += rating * review_count
                    builder_stats[user_token]['agent_details'].append({
                        'name': name or 'Unnamed',
                        'executions': exec_count,
                        'rating': rating
                    })
            except json.JSONDecodeError:
                continue
    
    return {
        'agents': agents,
        'agent_count': len(agents),
        'builder_count': len(builders),
        'total_executions': total_executions,
        'total_reviews': total_reviews,
        'total_weighted_rating': total_weighted_rating,
        'builder_stats': builder_stats,
        'agent_details': agent_details
    }

def analyze_group_c(cursor, exclusion_list):
    """Analyze Group C: Organic Public Agents (excluding paid traffic + Grant Program Builder agents)."""
    print("🅾️ Analyzing Group C: Organic Public Agents...")
    
    # Get all public agents
    cursor.execute("""
        SELECT agent_id, authors, executions, reviews_count, reviews_score, name
        FROM agents 
        WHERE status = 'public'
    """)
    
    all_agents = cursor.fetchall()
    
    # Filter out paid traffic and Grant Program Builder agents
    filtered_agents = []
    for agent_id, authors_json, executions, reviews_count, reviews_score, name in all_agents:
        # Skip paid traffic agents
        if agent_id in exclusion_list:
            continue
        
        # Skip Grant Program Builder agents
        cursor.execute("SELECT builder_grant_program FROM agents WHERE agent_id = ?", (agent_id,))
        result = cursor.fetchone()
        if result and result[0] == 1:
            continue
        
        filtered_agents.append((agent_id, authors_json, executions, reviews_count, reviews_score, name))
    
    # Extract builders and stats
    builder_stats = defaultdict(lambda: {
        'agent_count': 0, 'total_executions': 0, 'total_reviews': 0, 
        'total_weighted_rating': 0, 'agent_details': []
    })
    
    builders = set()
    total_executions = 0
    total_reviews = 0
    total_weighted_rating = 0
    agent_details = []
    
    for agent_id, authors_json, executions, reviews_count, reviews_score, name in filtered_agents:
        exec_count = executions or 0
        review_count = reviews_count or 0
        rating = reviews_score or 0
        
        total_executions += exec_count
        total_reviews += review_count
        if review_count > 0:
            total_weighted_rating += rating * review_count
        
        agent_details.append({
            'agent_id': agent_id,
            'name': name or 'Unnamed',
            'executions': exec_count,
            'reviews_count': review_count,
            'average_rating': rating
        })
        
        if authors_json:
            try:
                authors = json.loads(authors_json)
                for user_token in authors.keys():
                    builders.add(user_token)
                    builder_stats[user_token]['agent_count'] += 1
                    builder_stats[user_token]['total_executions'] += exec_count
                    builder_stats[user_token]['total_reviews'] += review_count
                    if review_count > 0:
                        builder_stats[user_token]['total_weighted_rating'] += rating * review_count
                    builder_stats[user_token]['agent_details'].append({
                        'name': name or 'Unnamed',
                        'executions': exec_count,
                        'rating': rating
                    })
            except json.JSONDecodeError:
                continue
    
    return {
        'agents': filtered_agents,
        'agent_count': len(filtered_agents),
        'builder_count': len(builders),
        'total_executions': total_executions,
        'total_reviews': total_reviews,
        'total_weighted_rating': total_weighted_rating,
        'builder_stats': builder_stats,
        'agent_details': agent_details
    }

def print_group_summary(group_name, group_data, total_public_agents):
    """Print summary statistics for a group."""
    avg_agents_per_builder = group_data['agent_count'] / group_data['builder_count'] if group_data['builder_count'] > 0 else 0
    avg_executions_per_agent = group_data['total_executions'] / group_data['agent_count'] if group_data['agent_count'] > 0 else 0
    avg_reviews_per_agent = group_data['total_reviews'] / group_data['agent_count'] if group_data['agent_count'] > 0 else 0
    avg_rating = group_data['total_weighted_rating'] / group_data['total_reviews'] if group_data['total_reviews'] > 0 else 0
    percentage = (group_data['agent_count'] / total_public_agents) * 100 if total_public_agents > 0 else 0
    
    print(f"\n{group_name}")
    print("=" * 60)
    print(f"Total Agents: {group_data['agent_count']:,} ({percentage:.1f}% of all public agents)")
    print(f"Total Builders: {group_data['builder_count']:,}")
    print(f"Average Agents per Builder: {avg_agents_per_builder:.1f}")
    print(f"Total Executions: {group_data['total_executions']:,}")
    print(f"Average Executions per Agent: {avg_executions_per_agent:,.0f}")
    print(f"Total Reviews: {group_data['total_reviews']:,}")
    print(f"Average Reviews per Agent: {avg_reviews_per_agent:.1f}")
    print(f"Average Review Score: {avg_rating:.2f}⭐")

def print_top_agents(group_name, agent_details):
    """Print top 10 agents by executions."""
    print(f"\n🏆 TOP 10 AGENTS - {group_name}")
    print("-" * 100)
    print(f"{'Rank':<5} {'Agent Name':<50} {'Executions':<12} {'Avg Rating':<10}")
    print("-" * 100)
    
    # Sort by executions
    sorted_agents = sorted(agent_details, key=lambda x: x['executions'], reverse=True)
    
    for i, agent in enumerate(sorted_agents[:10], 1):
        name = agent['name'][:47] + "..." if len(agent['name']) > 50 else agent['name']
        print(f"{i:<5} {name:<50} {agent['executions']:<12,} {agent['average_rating']:<10.2f}")

def print_top_builders(group_name, builder_stats):
    """Print top 10 builders by agent count."""
    print(f"\n🏆 TOP 10 BUILDERS - {group_name}")
    print("-" * 110)
    print(f"{'Rank':<5} {'User Token':<35} {'Agents':<8} {'Executions':<12} {'Avg Rating':<10}")
    print("-" * 110)
    
    # Sort by agent count
    sorted_builders = sorted(builder_stats.items(), key=lambda x: x[1]['agent_count'], reverse=True)
    
    for i, (user_token, stats) in enumerate(sorted_builders[:10], 1):
        avg_rating = (stats['total_weighted_rating'] / stats['total_reviews']) if stats['total_reviews'] > 0 else 0
        print(f"{i:<5} {user_token:<35} {stats['agent_count']:<8} {stats['total_executions']:<12,} {avg_rating:<10.2f}")

def main():
    """Main comparison analysis."""
    print("🔄 Loading Three Group Comparison Analysis")
    print("=" * 80)
    
    # Load exclusion list
    exclusion_list = load_exclusion_list()
    if not exclusion_list:
        print("❌ Cannot proceed without exclusion list.")
        return
    
    # Connect to database
    db_path = 'data/agents.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get total public agents count
    cursor.execute("SELECT COUNT(*) FROM agents WHERE status = 'public'")
    total_public_agents = cursor.fetchone()[0]
    
    print(f"Total public agents in database: {total_public_agents:,}")
    print(f"Paid traffic exclusion list: {len(exclusion_list)} agents")
    
    # Analyze each group
    group_a = analyze_group_a(cursor)
    group_b = analyze_group_b(cursor)
    group_c = analyze_group_c(cursor, exclusion_list)
    
    conn.close()
    
    # Print group summaries
    print(f"\n{'='*80}")
    print("📊 THREE GROUP COMPARISON SUMMARY")
    print(f"{'='*80}")
    
    print_group_summary("🅰️ GROUP A: GRANT PROGRAM BUILDERS", group_a, total_public_agents)
    print_group_summary("🅱️ GROUP B: ALL PUBLIC AGENTS", group_b, total_public_agents)
    print_group_summary("🅾️ GROUP C: ORGANIC PUBLIC AGENTS", group_c, total_public_agents)
    
    # Print top agents for each group
    print(f"\n{'='*80}")
    print("🏆 TOP PERFORMERS BY GROUP")
    print(f"{'='*80}")
    
    print_top_agents("GROUP A: GRANT PROGRAM BUILDERS", group_a['agent_details'])
    print_top_builders("GROUP A: GRANT PROGRAM BUILDERS", group_a['builder_stats'])
    
    print_top_agents("GROUP B: ALL PUBLIC AGENTS", group_b['agent_details'])
    print_top_builders("GROUP B: ALL PUBLIC AGENTS", group_b['builder_stats'])
    
    print_top_agents("GROUP C: ORGANIC PUBLIC AGENTS", group_c['agent_details'])
    print_top_builders("GROUP C: ORGANIC PUBLIC AGENTS", group_c['builder_stats'])
    
    print(f"\n🎯 ANALYSIS COMPLETE!")
    print("All three groups analyzed with comprehensive metrics and top performers identified.")

if __name__ == "__main__":
    main() 