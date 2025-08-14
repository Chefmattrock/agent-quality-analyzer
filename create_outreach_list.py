import sqlite3
import json
import csv
from typing import List, Dict, Any

def get_builder_info(user_token: str) -> Dict[str, Any]:
    """
    Get detailed information about a builder and their public agents. Ranking by Total public agents built.
    
    Args:
        user_token (str): The user token to search for
        
    Returns:
        dict: Builder information including name, Twitter, and public agents
    """
    conn = sqlite3.connect('data/agents.db')
    c = conn.cursor()
    
    # Get all public agents by this author
    c.execute('SELECT agent_id, name, description, authors, tags, executions, reviews_count, reviews_score FROM agents WHERE status = "public"')
    agents = c.fetchall()
    
    builder_info = {
        'user_token': user_token,
        'name': 'Unknown',
        'twitter': '',
        'email': '',  # We'll need to extract from user_token or other sources
        'public_agents': []
    }
    
    for agent in agents:
        agent_id, name, description, authors_json, tags_json, executions, reviews_count, reviews_score = agent
        
        try:
            authors = json.loads(authors_json) if authors_json else {}
            
            # Check if this agent is authored by our target user
            if user_token in authors:
                # Store builder info from the first agent we find
                if builder_info['name'] == 'Unknown':
                    author_data = authors[user_token]
                    builder_info['name'] = author_data.get('name', 'Unknown')
                    builder_info['twitter'] = author_data.get('twitter_username', '')
                
                # Store agent info
                tags = json.loads(tags_json) if tags_json else []
                builder_info['public_agents'].append({
                    'agent_id': agent_id,
                    'name': name,
                    'description': description,
                    'tags': tags,
                    'executions': executions or 0,
                    'reviews_count': reviews_count or 0,
                    'reviews_score': reviews_score or 0
                })
        except json.JSONDecodeError:
            continue
    
    conn.close()
    return builder_info

def main():
    # List of builders to analyze
    builders = [
        "6619b6e922524415b42a5b96ef4dd320",  # Chris Shuptrine
        "4dc11027776d484c92b6b13cd3a1013c",  # Dominik Sigmund
        "cbd505fdf0964b5c",  # @SurajKripalani
        "493373b53fda4d12",  # Nishith
        "bc338ed620ef4638bc6c5a9c725f80e0",  # Jeff Ocaya
        "4c60aa833303457a",  # Enrich Labs
        "18e877934c414317",  # Lee H
        "68a7d7ebe431418bb8e8c22963cd7c56",  # Meghan O'Keefe
        "fcc120e3cab948c6",  # VAMSHI REDDY
        "98d8f13f37144549",  # Christopher Kiper
        "$device:19552f33e11bce-06ca8fc100198f-b457453-46500-19552f33e11bce",  # Ashna Thakkar
        "58ea52ad3b2a4df6",  # @uussamaab
        "0558ee5500dc458784239019d6e77f51",  # Brandon Smith
        "a646e3d230264200",  # William Mulcahy
        "c87c458d52754180",  # Rick Flores
        "18b51e30a5074e93",  # Dhruv Atreja
        "b36efea733894a6e",  # Clint Fontanella
        "e55c3645ebe9487b",  # Nishit Maheta
    ]
    
    print("Building Outreach List for Top Agent Builders")
    print("=" * 100)
    
    all_builders_data = []
    
    for user_token in builders:
        print(f"\nProcessing builder: {user_token}")
        builder_info = get_builder_info(user_token)
        
        if builder_info['public_agents']:
            print(f"  Found {len(builder_info['public_agents'])} public agents")
            print(f"  Name: {builder_info['name']}")
            print(f"  Twitter: @{builder_info['twitter']}" if builder_info['twitter'] else "  Twitter: None")
            
            all_builders_data.append(builder_info)
        else:
            print(f"  No public agents found")
    
    # Save to CSV
    csv_filename = 'data/outreach_builders.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'user_token', 'name', 'twitter', 'email',
            'total_public_agents', 'total_executions', 'total_reviews',
            'avg_review_score', 'top_tags', 'agent_list'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for builder in all_builders_data:
            agents = builder['public_agents']
            
            # Calculate totals
            total_executions = sum(agent['executions'] for agent in agents)
            total_reviews = sum(agent['reviews_count'] for agent in agents)
            avg_review_score = sum(agent['reviews_score'] for agent in agents) / len(agents) if agents else 0
            
            # Get top tags
            all_tags = []
            for agent in agents:
                all_tags.extend(agent['tags'])
            tag_counts = {}
            for tag in all_tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
            top_tags = ', '.join(sorted(tag_counts.keys(), key=lambda x: tag_counts[x], reverse=True)[:5])
            
            # Create agent list
            agent_list = '; '.join([f"{agent['name']} ({agent['executions']} execs, {agent['reviews_count']} reviews)" for agent in agents])
            
            writer.writerow({
                'user_token': builder['user_token'],
                'name': builder['name'],
                'twitter': builder['twitter'],
                'email': builder['email'],
                'total_public_agents': len(agents),
                'total_executions': total_executions,
                'total_reviews': total_reviews,
                'avg_review_score': round(avg_review_score, 2),
                'top_tags': top_tags,
                'agent_list': agent_list
            })
    
    print(f"\n" + "=" * 100)
    print(f"Outreach list saved to: {csv_filename}")
    print(f"Total builders processed: {len(all_builders_data)}")
    
    # Display summary
    print(f"\nSummary:")
    for builder in all_builders_data:
        agents = builder['public_agents']
        total_executions = sum(agent['executions'] for agent in agents)
        total_reviews = sum(agent['reviews_count'] for agent in agents)
        
        print(f"  {builder['name']} (@{builder['twitter']}): {len(agents)} agents, {total_executions} total executions, {total_reviews} total reviews")

if __name__ == "__main__":
    main() 