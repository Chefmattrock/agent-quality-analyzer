import sqlite3
import json
import csv
import pandas as pd
from typing import List, Dict, Any
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file in root directory
project_root = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=env_path, override=True)

def load_email_mappings():
    """
    Load email addresses from existing CSV files to map user tokens to emails.
    """
    email_mappings = {}
    
    # Load from grant program builders file
    try:
        grant_df = pd.read_csv('data/grant_program_builders_summary_fixed.csv')
        for _, row in grant_df.iterrows():
            email = row.iloc[0]  # First column is email
            user_token = row.iloc[1]  # Second column is user token
            if pd.notna(email) and pd.notna(user_token):
                email_mappings[user_token] = email
    except Exception as e:
        print(f"Warning: Could not load grant program data: {e}")
    
    # Load from HubSpot export
    try:
        hubspot_df = pd.read_csv('data/hubspot-crm-exports-nytw-approved-guests-2025-06-13.csv')
        for _, row in hubspot_df.iterrows():
            email = row['Email']
            user_token = row['Platform User Token']
            if pd.notna(email) and pd.notna(user_token) and user_token:
                email_mappings[user_token] = email
    except Exception as e:
        print(f"Warning: Could not load HubSpot data: {e}")
    
    return email_mappings

def get_hubspot_contact_info(email: str, api_key: str = None) -> Dict[str, Any]:
    """
    Get HubSpot contact information for an email address.
    
    Args:
        email (str): Email address to look up
        api_key (str): HubSpot API key (optional)
        
    Returns:
        dict: Contact information including LinkedIn URL and last activity
    """
    if not api_key:
        api_key = os.getenv('HUB_API_KEY')
    
    if not api_key:
        print(f"  No HubSpot API key found. Set HUB_API_KEY in your .env file")
        return {
            'linkedin_url': '',
            'last_activity_date': '',
            'company': '',
            'job_title': ''
        }
    
    try:
        # Search for contact by email
        search_url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        search_data = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "email",
                            "operator": "EQ",
                            "value": email
                        }
                    ]
                }
            ],
            "properties": ["email", "firstname", "lastname", "linkedin_url", "lastmodifieddate", "company", "jobtitle"]
        }
        
        response = requests.post(search_url, headers=headers, json=search_data)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                contact = data['results'][0]
                properties = contact.get('properties', {})
                
                return {
                    'linkedin_url': properties.get('linkedin_url', ''),
                    'last_activity_date': properties.get('lastmodifieddate', ''),
                    'company': properties.get('company', ''),
                    'job_title': properties.get('jobtitle', '')
                }
        
        return {
            'linkedin_url': '',
            'last_activity_date': '',
            'company': '',
            'job_title': ''
        }
        
    except Exception as e:
        print(f"Error fetching HubSpot data for {email}: {e}")
        return {
            'linkedin_url': '',
            'last_activity_date': '',
            'company': '',
            'job_title': ''
        }

def get_builder_info(user_token: str, email_mappings: Dict[str, str]) -> Dict[str, Any]:
    """
    Get detailed information about a builder and their public agents.
    
    Args:
        user_token (str): The user token to search for
        email_mappings (dict): Mapping of user tokens to email addresses
        
    Returns:
        dict: Builder information including name, Twitter, email, and public agents
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
        'email': email_mappings.get(user_token, ''),
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
    
    print("Building Enhanced Outreach List for Top Agent Builders")
    print("=" * 100)
    
    # Load email mappings
    print("Loading email mappings...")
    email_mappings = load_email_mappings()
    print(f"Found {len(email_mappings)} email mappings")
    
    all_builders_data = []
    
    for user_token in builders:
        print(f"\nProcessing builder: {user_token}")
        builder_info = get_builder_info(user_token, email_mappings)
        
        if builder_info['public_agents']:
            print(f"  Found {len(builder_info['public_agents'])} public agents")
            print(f"  Name: {builder_info['name']}")
            print(f"  Twitter: @{builder_info['twitter']}" if builder_info['twitter'] else "  Twitter: None")
            print(f"  Email: {builder_info['email']}" if builder_info['email'] else "  Email: Not found")
            
            # Get HubSpot data if we have an email
            if builder_info['email']:
                print(f"  Fetching HubSpot data for {builder_info['email']}...")
                hubspot_data = get_hubspot_contact_info(builder_info['email'])
                builder_info.update(hubspot_data)
                print(f"  LinkedIn: {hubspot_data['linkedin_url']}" if hubspot_data['linkedin_url'] else "  LinkedIn: Not found")
                print(f"  Last Activity: {hubspot_data['last_activity_date']}" if hubspot_data['last_activity_date'] else "  Last Activity: Not found")
            
            all_builders_data.append(builder_info)
        else:
            print(f"  No public agents found")
    
    # Save to CSV
    csv_filename = 'data/enhanced_outreach_builders.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'user_token', 'name', 'twitter', 'email', 'linkedin_url', 'last_activity_date', 'company', 'job_title',
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
                'linkedin_url': builder.get('linkedin_url', ''),
                'last_activity_date': builder.get('last_activity_date', ''),
                'company': builder.get('company', ''),
                'job_title': builder.get('job_title', ''),
                'total_public_agents': len(agents),
                'total_executions': total_executions,
                'total_reviews': total_reviews,
                'avg_review_score': round(avg_review_score, 2),
                'top_tags': top_tags,
                'agent_list': agent_list
            })
    
    print(f"\n" + "=" * 100)
    print(f"Enhanced outreach list saved to: {csv_filename}")
    print(f"Total builders processed: {len(all_builders_data)}")
    
    # Display summary
    print(f"\nSummary:")
    for builder in all_builders_data:
        agents = builder['public_agents']
        total_executions = sum(agent['executions'] for agent in agents)
        total_reviews = sum(agent['reviews_count'] for agent in agents)
        
        print(f"  {builder['name']} (@{builder['twitter']}): {len(agents)} agents, {total_executions} total executions, {total_reviews} total reviews")
        if builder['email']:
            print(f"    Email: {builder['email']}")
        if builder.get('linkedin_url'):
            print(f"    LinkedIn: {builder['linkedin_url']}")

if __name__ == "__main__":
    main() 