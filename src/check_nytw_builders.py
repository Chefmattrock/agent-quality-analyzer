#!/usr/bin/env python3
"""
Check NYTW attendees against HubSpot to get their platform_user_tokens.
"""

import os
import sys
import pandas as pd
import requests
import json
import logging
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('nytw_hubspot_check.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
HUB_API_KEY = os.getenv('HUB_API_KEY')

def create_session_with_retries():
    """Create a requests session with retry logic."""
    session = requests.Session()
    retry_strategy = requests.adapters.Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def get_platform_token_from_hubspot(email: str, session) -> str:
    """Get platform_user_token from HubSpot for a given email."""
    headers = {
        "Authorization": f"Bearer {HUB_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # HubSpot search API endpoint
    search_url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
    
    # Create search query
    body = {
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
        "properties": ["platform_user_token", "email", "firstname", "lastname"]
    }
    
    try:
        response = session.post(search_url, headers=headers, json=body, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        results = data.get('results', [])
        
        if results:
            props = results[0].get('properties', {})
            return props.get('platform_user_token')
        
        return None
        
    except Exception as e:
        logger.error(f"Error querying HubSpot for {email}: {str(e)}")
        return None

def main():
    # Read unmatched emails
    try:
        with open('unmatched_nytw_attendees.txt', 'r') as f:
            emails = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.error("unmatched_nytw_attendees.txt not found")
        return
    
    # Take first 100 emails
    test_emails = emails[:100]
    logger.info(f"Processing {len(test_emails)} emails")
    
    # Create session with retry logic
    session = create_session_with_retries()
    
    # Process emails
    results = []
    for i, email in enumerate(test_emails, 1):
        logger.info(f"Processing {i}/100: {email}")
        token = get_platform_token_from_hubspot(email, session)
        
        results.append({
            'email': email,
            'platform_user_token': token
        })
        
        # Small delay to be nice to HubSpot API
        time.sleep(0.1)
    
    # Save results
    df = pd.DataFrame(results)
    df.to_csv('data/100_test_builders.csv', index=False)
    
    # Log summary
    found_tokens = df['platform_user_token'].notna().sum()
    logger.info(f"\n=== Processing Summary ===")
    logger.info(f"Total emails processed: {len(test_emails)}")
    logger.info(f"Found platform tokens: {found_tokens}")
    logger.info(f"Missing platform tokens: {len(test_emails) - found_tokens}")
    logger.info(f"Results saved to data/100_test_builders.csv")

if __name__ == "__main__":
    main() 