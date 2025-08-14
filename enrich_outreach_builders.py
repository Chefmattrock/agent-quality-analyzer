#!/usr/bin/env python3
"""
Enrich Outreach Builders CSV with HubSpot Data

This script fetches LinkedIn URLs and Last platform activity dates from HubSpot
for all contacts in the data/outreach_builders.csv file and adds them as new columns.

USAGE:
    python enrich_outreach_builders.py

REQUIREMENTS:
- HUB_API_KEY in .env file
- data/outreach_builders.csv file with email column

ADDS:
- linkedin_url: LinkedIn profile URL from HubSpot
- last_platform_activity_date: Last platform activity date from HubSpot
"""

import pandas as pd
import requests
import os
import sys
from dotenv import load_dotenv
import time
from typing import Dict, Optional

# Load environment variables
load_dotenv()

# Get HubSpot API key from environment
HUBSPOT_API_KEY = os.getenv("HUB_API_KEY")

class HubSpotEnricher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.hubapi.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_contact_by_email(self, email: str) -> Dict[str, Optional[str]]:
        """Get contact information by email address"""
        if not email or pd.isna(email):
            return {"linkedin_url": None, "last_platform_activity_date": None}
            
        url = f"{self.base_url}/crm/v3/objects/contacts/search"
        
        # Search for contact by email
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
            "properties": [
                "linkedin_url",
                "linkedinbio",  # Alternative LinkedIn field
                "last_platform_activity_date",
                "hs_analytics_last_url"  # Alternative activity field
            ],
            "limit": 1
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=body)
            
            if response.status_code == 401:
                print(f"Error: Authentication failed. Check your HUB_API_KEY.")
                return {"linkedin_url": None, "last_platform_activity_date": None}
            
            if response.status_code == 429:
                print(f"Rate limit hit for {email}. Waiting 10 seconds...")
                time.sleep(10)
                # Retry once
                response = requests.post(url, headers=self.headers, json=body)
            
            if response.status_code != 200:
                print(f"Warning: Status code {response.status_code} for {email}")
                return {"linkedin_url": None, "last_platform_activity_date": None}
            
            data = response.json()
            results = data.get('results', [])
            
            if not results:
                print(f"Warning: No contact found for {email}")
                return {"linkedin_url": None, "last_platform_activity_date": None}
                
            contact = results[0]
            props = contact.get('properties', {})
            
            # Get LinkedIn URL (try multiple fields)
            linkedin_url = (props.get('linkedin_url') or 
                          props.get('linkedinbio') or 
                          None)
            
            # Get last platform activity date
            last_activity = (props.get('last_platform_activity_date') or 
                           props.get('hs_analytics_last_url') or 
                           None)
            
            return {
                "linkedin_url": linkedin_url,
                "last_platform_activity_date": last_activity
            }
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {email}: {str(e)}")
            return {"linkedin_url": None, "last_platform_activity_date": None}

def enrich_outreach_builders(input_file: str = "data/outreach_builders.csv", 
                           output_file: str = "data/outreach_builders_enriched.csv"):
    """Add HubSpot LinkedIn URL and last platform activity date to outreach builders CSV"""
    
    if not HUBSPOT_API_KEY:
        print("Error: HUB_API_KEY not found in environment variables")
        print("Please set HUB_API_KEY in your .env file")
        return False
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        return False
    
    # Read the CSV file
    print(f"Reading {input_file}...")
    try:
        # Use more robust CSV parsing for complex data
        df = pd.read_csv(input_file, 
                        quotechar='"', 
                        escapechar='\\',
                        doublequote=True,
                        skipinitialspace=True)
        print(f"Loaded {len(df)} rows")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        print("Trying alternative parsing method...")
        try:
            # Try reading with Python's csv module first
            import csv
            rows = []
            with open(input_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
            df = pd.DataFrame(rows)
            print(f"Loaded {len(df)} rows using csv module")
        except Exception as e2:
            print(f"Both parsing methods failed: {e2}")
            return False
    
    print(f"Available columns: {list(df.columns)}")
    
    if 'email' not in df.columns:
        print("Error: 'email' column not found in CSV file")
        return False
    
    # Check email column for valid emails
    # Convert email column to string first to handle mixed types
    df['email'] = df['email'].astype(str)
    
    # Debug: Show first few email values
    print("First 5 email values:")
    for i in range(min(5, len(df))):
        print(f"  Row {i}: '{df.iloc[i]['email']}'")
    
    valid_emails = df[(df['email'] != 'nan') & (df['email'] != '') & (df['email'].str.strip() != '')]
    print(f"Found {len(valid_emails)} rows with valid email addresses out of {len(df)} total rows")
    
    # Initialize HubSpot client
    enricher = HubSpotEnricher(HUBSPOT_API_KEY)
    
    # Add new columns
    df['linkedin_url'] = None
    df['last_platform_activity_date'] = None
    
    # Process each email
    total_emails = len(df)
    successful_enrichments = 0
    
    print(f"Processing {total_emails} contacts...")
    
    for index, row in df.iterrows():
        email = row['email']
        
        # Skip if email is empty/nan
        if email == 'nan' or email == '' or email.strip() == '':
            print(f"Processing {index + 1}/{total_emails}: (skipping - no email)")
            continue
            
        print(f"Processing {index + 1}/{total_emails}: {email}")
        
        # Get HubSpot data
        hubspot_data = enricher.get_contact_by_email(email)
        
        # Update DataFrame
        df.at[index, 'linkedin_url'] = hubspot_data['linkedin_url']
        df.at[index, 'last_platform_activity_date'] = hubspot_data['last_platform_activity_date']
        
        # Track successful enrichments
        if hubspot_data['linkedin_url'] or hubspot_data['last_platform_activity_date']:
            successful_enrichments += 1
        
        # Rate limiting - HubSpot allows 100 requests per 10 seconds
        # Being conservative with 90 requests per 10 seconds
        if (index + 1) % 90 == 0:
            print("Rate limiting - waiting 10 seconds...")
            time.sleep(10)
        else:
            # Small delay between requests
            time.sleep(0.1)
    
    # Save the enriched CSV
    print(f"\nSaving enriched data to {output_file}...")
    try:
        df.to_csv(output_file, index=False)
        print(f"Successfully saved enriched data!")
        print(f"Total contacts processed: {total_emails}")
        print(f"Successful enrichments: {successful_enrichments}")
        print(f"Success rate: {successful_enrichments/total_emails*100:.1f}%")
        return True
    except Exception as e:
        print(f"Error saving CSV file: {e}")
        return False

def main():
    """Main function to run the enrichment process"""
    input_file = "data/outreach_builders_fixed.csv"
    output_file = "data/outreach_builders_enriched.csv"
    
    print("HubSpot Outreach Builders Enrichment Tool")
    print("=" * 50)
    
    success = enrich_outreach_builders(input_file, output_file)
    
    if success:
        print("\n✅ Enrichment completed successfully!")
        print(f"📄 Original file: {input_file}")
        print(f"📄 Enriched file: {output_file}")
    else:
        print("\n❌ Enrichment failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 