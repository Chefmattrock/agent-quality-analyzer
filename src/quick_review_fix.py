#!/usr/bin/env python3
import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('data/agents.db')
cursor = conn.cursor()

# Get all Grant Program Builder agents
cursor.execute("""
    SELECT agent_id, agent_id_human, name, executions, reviews_count, reviews_score, price
    FROM agents 
    WHERE builder_grant_program = 1
""")
builder_agents = cursor.fetchall()

print("🔍 Grant Program Builder Agents - Fixed Review Analysis")
print("=" * 60)

total_agents = len(builder_agents)
agents_with_reviews = [agent for agent in builder_agents if (agent[4] or 0) > 0]
agents_without_reviews = total_agents - len(agents_with_reviews)

print(f"Total Grant Program Builder agents: {total_agents}")
print(f"Agents with reviews: {len(agents_with_reviews)}")
print(f"Agents without reviews: {agents_without_reviews}")

if agents_with_reviews:
    # Calculate weighted average rating ONLY for agents with reviews
    total_weighted_rating = sum(agent[5] * agent[4] for agent in agents_with_reviews)
    total_reviews = sum(agent[4] for agent in agents_with_reviews)
    
    corrected_avg_rating = total_weighted_rating / total_reviews
    
    print(f"\n📊 CORRECTED REVIEW STATISTICS:")
    print(f"Average rating (only agents with reviews): {corrected_avg_rating:.2f}")
    print(f"Total reviews: {total_reviews:,}")
    print(f"Review coverage: {(len(agents_with_reviews)/total_agents)*100:.1f}% of agents have reviews")
    
    # Show some examples
    print(f"\n📋 SAMPLE AGENTS WITH REVIEWS:")
    print(f"{'Agent ID':<15} {'Name':<30} {'Reviews':<8} {'Rating':<8}")
    print("-" * 65)
    
    # Sort by rating and show top 5
    sorted_agents = sorted(agents_with_reviews, key=lambda x: x[5], reverse=True)[:5]
    for agent in sorted_agents:
        agent_id = agent[1] or agent[0][:12]
        name = (agent[2] or "No name")[:29]
        reviews = agent[4]
        rating = agent[5]
        print(f"{agent_id:<15} {name:<30} {reviews:<8} {rating:<8.2f}")
        
else:
    print(f"\nNo Grant Program Builder agents have reviews yet.")

conn.close() 