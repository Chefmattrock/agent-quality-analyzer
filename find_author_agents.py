import sqlite3
import json

def find_agents_by_author(user_token):
    """
    Find all agents authored by a specific user token.
    
    Args:
        user_token (str): The user token to search for
    """
    conn = sqlite3.connect('data/agents.db')
    c = conn.cursor()
    
    # Get all agents
    c.execute('SELECT agent_id, name, description, authors, status, tags FROM agents')
    agents = c.fetchall()
    
    authored_agents = []
    
    for agent in agents:
        agent_id, name, description, authors_json, status, tags_json = agent
        
        try:
            authors = json.loads(authors_json) if authors_json else {}
            
            # Check if the user token is in the authors
            if user_token in authors:
                authored_agents.append({
                    'agent_id': agent_id,
                    'name': name,
                    'description': description,
                    'author_info': authors[user_token],
                    'status': status,
                    'tags': json.loads(tags_json) if tags_json else []
                })
        except json.JSONDecodeError:
            continue
    
    conn.close()
    return authored_agents

def main():
    user_token = "2fcfc742e174448298195899a0ba75bf"
    
    print(f"Searching for agents authored by user token: {user_token}")
    print("=" * 80)
    
    agents = find_agents_by_author(user_token)
    
    if not agents:
        print("No agents found for this user token.")
        return
    
    print(f"Found {len(agents)} agent(s):\n")
    
    for i, agent in enumerate(agents, 1):
        print(f"{i}. Agent ID: {agent['agent_id']}")
        print(f"   Name: {agent['name']}")
        print(f"   Status: {agent['status']}")
        print(f"   Author: {agent['author_info'].get('name', 'Unknown')}")
        if agent['author_info'].get('twitter_username'):
            print(f"   Twitter: @{agent['author_info']['twitter_username']}")
        print(f"   Tags: {', '.join(agent['tags']) if agent['tags'] else 'None'}")
        print(f"   Description: {agent['description'][:200]}{'...' if len(agent['description']) > 200 else ''}")
        print("-" * 80)

if __name__ == "__main__":
    main() 