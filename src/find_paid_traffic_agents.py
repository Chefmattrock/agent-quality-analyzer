#!/usr/bin/env python3
"""
Paid Traffic Agents Finder

PURPOSE:
This script finds Agent_IDs for agents that receive paid traffic.
These will be excluded from Group C analysis.

WHAT IT DOES:
1. Takes a list of agent names that receive paid traffic
2. Searches the database for matching agents by name
3. Returns Agent_IDs for the exclusion list
4. Creates Group C exclusion list
"""

import sqlite3
import pandas as pd
from difflib import SequenceMatcher

def similarity(a, b):
    """Calculate similarity between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_paid_traffic_agents():
    """Find Agent_IDs for agents that receive paid traffic."""
    
    # Updated list of paid traffic agent names (with corrections and removals)
    paid_traffic_agents = [
        "LLM-Feature-Activation Prompt Generator",
        "Topic Sentiment Analyzer", 
        "Icon Designer",
        "SEO Performance Gap Analysis",
        "Newsletter Curator Agent (News Roundup Newsletter Generator)",
        "Prompt Enhancer & Optimizer",
        "Meeting Agenda Generator",
        "Sales Call Coach",
        "Raw Data to Structured JSON Formatter",
        "Critical Thinking Improver (Paul-Elder Framework)",
        "Agent.ai HTML Output Builder",
        "YouTube Title Generator",
        "Sample dataset",
        "Explain Any Technical Concept in Simple Terms",
        "Feedback Polisher",
        "Sales Engineer Call Next Step Generator",
        "Outrank Competitor Pages with SEO Recommendations",
        "Custom ICP Generator and Target Company Grader",
        "Podcast Recommender",
        "Proposal Writer",
        "Identify Problems With Your Target Audience",
        "Craft LinkedIn Recommendations",
        "Company Research Pro",
        "SWOT Analysis",
        "Webinar Content Planner",
        "Software Contract Reviewer",
        "Trending Topic Blog Suggestions",
        "Create Useful Prompts to Use in Your Job",
        "Value Proposition Canvas (Strategyzer)",
        "Running Late Rescue Agent",
        "Sales Battle Cards",
        "Followup Email Gen",
        "Transcript Generator (Social Posts, blog posts)",
        "3 So What's",
        "Executive DISC Profile",
        "Flux Image Generator",
        "Meme Maker",
        "Competitor Analyst",
        "Company Research",
        "Search KeyWord Research",
        "SEO Content Optimizer",
        "Website Domain Valuation Expert",
        "Open AI 4.1 Agent",
        # Updated/corrected names below:
        "Knowledge Base Audit (Improve your Support Docs)",
        "Competitive Intelligence Market Research Assistant",
        "Startup Pitch deck Grader",
        "promote product or feature pages with pain point generator",
        "new home construction cost estimator",
        "Local Zoning ordinance summary (for architects, builders, real estate)",
        "Mission Statement and Motto / Tagline Generator",
        "Programs and Activities to enrich company culture",
        "Online Price Comparer (compare prices with many sellers)",
        "Course Finder (Learn anything for Work)",
        "LLM Visibility Checker (Is your Robots.txt blocking LLMs)",
        "Exercise Assistant: Where should I bike/run/walk?",
        "News Article / URL summarizer & Fact Checker",
        "Blog Post Rewriter / Repurposer",
        "Transcript to Podcast Title & Description Agent",
        "Rival Watch - Competitor Alert System",
        "Sales Call Prepper - Industry Insights",
        "Introductory Call Rapport Builder Agent",
        "Company Research w/ Citations - Website Output",
        "Podcast Prep Agent (Podcast Outline Generator)",
        "Business Logo inspiration",
        "Agent PopK - Trendy Songs turned Kid-Friendly!",
        "Customer Persona Builder",
        "Twitter/X Personality Analyzer",
        "EarningsWhiz 6Q - Earnings Call Analyzer",
        "SEO-Optimized Content Generator",
        "Ideogram Image Generator"
    ]
    
    print("🔍 Finding Agent_IDs for Paid Traffic Agents (Group C Exclusion List)")
    print("=" * 75)
    print(f"Searching for {len(paid_traffic_agents)} unique agent names...")
    
    db_path = 'data/agents.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all agent names and IDs
    cursor.execute("SELECT agent_id, name FROM agents WHERE status = 'public'")
    all_agents = cursor.fetchall()
    
    found_agents = []
    not_found = []
    
    print(f"\n📊 Searching through {len(all_agents)} public agents...")
    
    for target_name in paid_traffic_agents:
        best_match = None
        best_similarity = 0
        
        # Look for exact matches first
        exact_matches = [agent for agent in all_agents if agent[1] and agent[1].lower() == target_name.lower()]
        
        if exact_matches:
            agent_id, name = exact_matches[0]
            found_agents.append({
                'target_name': target_name,
                'found_name': name,
                'agent_id': agent_id,
                'match_type': 'exact',
                'similarity': 1.0
            })
            print(f"✅ EXACT: '{target_name}' -> {agent_id}")
        else:
            # Look for partial matches
            for agent_id, name in all_agents:
                if name:
                    sim = similarity(target_name, name)
                    if sim > best_similarity and sim > 0.8:  # 80% similarity threshold
                        best_similarity = sim
                        best_match = (agent_id, name)
            
            if best_match:
                agent_id, name = best_match
                found_agents.append({
                    'target_name': target_name,
                    'found_name': name,
                    'agent_id': agent_id,
                    'match_type': 'similar',
                    'similarity': best_similarity
                })
                print(f"🔍 SIMILAR ({best_similarity:.2f}): '{target_name}' -> '{name}' -> {agent_id}")
            else:
                not_found.append(target_name)
                print(f"❌ NOT FOUND: '{target_name}'")
    
    conn.close()
    
    # Results summary
    print(f"\n{'='*75}")
    print("📊 PAID TRAFFIC AGENTS SEARCH RESULTS")
    print(f"{'='*75}")
    print(f"Total agents searched for: {len(paid_traffic_agents)}")
    print(f"Found (exact matches): {len([a for a in found_agents if a['match_type'] == 'exact'])}")
    print(f"Found (similar matches): {len([a for a in found_agents if a['match_type'] == 'similar'])}")
    print(f"Not found: {len(not_found)}")
    print(f"Total found: {len(found_agents)}")
    
    if not_found:
        print(f"\n❌ AGENTS STILL NOT FOUND:")
        for name in not_found:
            print(f"   - {name}")
    
    # Export results
    print(f"\n📁 Exporting results...")
    
    # Export found agents with details
    if found_agents:
        df = pd.DataFrame(found_agents)
        df.to_csv('paid_traffic_agents_found.csv', index=False)
        print(f"✅ Found agents exported to: paid_traffic_agents_found.csv")
        
        # Export just the Agent_IDs for exclusion list
        agent_ids = [agent['agent_id'] for agent in found_agents]
        ids_df = pd.DataFrame({'agent_id': agent_ids})
        ids_df.to_csv('paid_traffic_exclusion_list.csv', index=False)
        print(f"✅ Exclusion list exported to: paid_traffic_exclusion_list.csv")
        
        print(f"\n🎯 GROUP C EXCLUSION LIST READY!")
        print(f"   {len(agent_ids)} agents will be excluded from Group C analysis")
        
        return agent_ids
    else:
        print("❌ No agents found to create exclusion list")
        return []

if __name__ == "__main__":
    exclusion_ids = find_paid_traffic_agents()
    
    if exclusion_ids:
        print(f"\n📋 EXCLUSION LIST PREVIEW (first 10):")
        for i, agent_id in enumerate(exclusion_ids[:10], 1):
            print(f"   {i}. {agent_id}")
        if len(exclusion_ids) > 10:
            print(f"   ... and {len(exclusion_ids) - 10} more")
    
    print(f"\n🚀 Ready to create Group C: Public agents excluding paid traffic agents!") 