#!/usr/bin/env python3
"""
HubSpot List Contact Extractor

PURPOSE:
This script fetches email addresses and platform_user_tokens for all contacts 
in a specific HubSpot list. It's designed to extract builder/user information 
from curated HubSpot marketing lists.

USAGE:
    python get_builder_ids.py

WHAT IT DOES:
- Connects to HubSpot API using HUB_API_KEY from .env
- Fetches all contacts from HubSpot list ID 301 (hardcoded)
- Extracts email and platform_user_token for each contact
- Displays results in a formatted table
- Only shows contacts that have BOTH email and platform_user_token

REQUIREMENTS:
- HUB_API_KEY in .env file
- Access to the specified HubSpot list (currently list 301)

OUTPUT:
Displays a formatted table showing:
- Email address
- Platform user token

Note: The list ID is currently hardcoded to 301. This was created to extract
specific builder contacts from HubSpot marketing lists for analysis.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
HUB_API_KEY = os.getenv('HUB_API_KEY')

def fetch_contacts_from_list(list_id):
    """
    Fetch all contacts from a HubSpot list with their email and platform_user_token.
    """
    if not HUB_API_KEY:
        print("Error: HUB_API_KEY not set in .env file.")
        sys.exit(1)
    
    # Use the Lists API v1 to get list contacts (fetch all properties)
    url = f"https://api.hubapi.com/contacts/v1/lists/{list_id}/contacts/all"
    headers = {
        "Authorization": f"Bearer {HUB_API_KEY}",
        "Content-Type": "application/json"
    }
    
    all_contacts = []
    vid_offset = None
    total_contacts_processed = 0
    
    while True:
        params = {
            "count": 100,  # Maximum allowed by HubSpot API
            "property": ["email", "platform_user_token"]  # Explicitly request these properties
        }
        
        if vid_offset:
            params["vidOffset"] = vid_offset
            
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 401:
                print("Error: Authentication failed. Check your HUB_API_KEY.")
                sys.exit(1)
            elif response.status_code == 404:
                print(f"Error: List with ID {list_id} not found.")
                sys.exit(1)
            elif response.status_code != 200:
                print(f"Error: Status code {response.status_code}")
                print(response.text)
                sys.exit(1)
                
            data = response.json()
            contacts = data.get('contacts', [])
            
            if not contacts:
                break
                
            # Process each contact
            for contact in contacts:
                total_contacts_processed += 1
                properties = contact.get('properties', {})
                
                # Extract email
                email_prop = properties.get('email', {})
                email = email_prop.get('value') if email_prop else None
                
                # Extract platform_user_token
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
            print(f"Error fetching contacts from list: {e}")
            sys.exit(1)
    
    return all_contacts

def main():
    """
    Main function to fetch and display contacts from HubSpot list 301.
    """
    list_id = 301
    
    print(f"Fetching contacts from HubSpot list {list_id}...")
    contacts = fetch_contacts_from_list(list_id)
    
    if not contacts:
        print("No contacts found or no contacts have both email and platform_user_token.")
        return
    
    print(f"\nFound {len(contacts)} contacts with both email and platform_user_token:")
    print("-" * 80)
    print(f"{'Email':<40} {'Platform User Token':<40}")
    print("-" * 80)
    
    for contact in contacts:
        email = contact['email']
        token = contact['platform_user_token']
        print(f"{email:<40} {token:<40}")
    
    print("-" * 80)
    print(f"Total: {len(contacts)} contacts")

if __name__ == "__main__":
    main() 