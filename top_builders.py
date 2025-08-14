import sqlite3
import json
from collections import Counter

def get_top_builders():
    """
    Find all builders by number of public agents created.
    """
    conn = sqlite3.connect('data/agents.db')
    c = conn.cursor()
    
    # Get all public agents
    c.execute('SELECT authors FROM agents WHERE status = "public"')
    agents = c.fetchall()
    
    # Count agents per author
    author_counts = Counter()
    author_info = {}
    
    for (authors_json,) in agents:
        try:
            authors = json.loads(authors_json) if authors_json else {}
            
            for user_token, info in authors.items():
                author_counts[user_token] += 1
                # Store author info for display
                if user_token not in author_info:
                    author_info[user_token] = {
                        'name': info.get('name', 'Unknown'),
                        'twitter': info.get('twitter_username', ''),
                        'avatar': info.get('avatar', '')
                    }
        except json.JSONDecodeError:
            continue
    
    conn.close()
    
    # Get all builders sorted by count
    all_builders = author_counts.most_common()
    
    return all_builders, author_info

def main():
    print("Builders Ranked 21-40 by Number of Public Agents Created")
    print("=" * 80)
    
    all_builders, author_info = get_top_builders()
    
    # Get builders 21-40 (indices 20-39)
    builders_21_40 = all_builders[20:40]
    
    for i, (user_token, count) in enumerate(builders_21_40, 21):
        info = author_info.get(user_token, {})
        name = info.get('name', 'Unknown')
        twitter = info.get('twitter', '')
        
        print(f"{i:2d}. {name}")
        print(f"    User Token: {user_token}")
        if twitter:
            print(f"    Twitter: @{twitter}")
        print(f"    Public Agents: {count}")
        print("-" * 80)

if __name__ == "__main__":
    main() 