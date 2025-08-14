import pandas as pd
import requests
import os
import sys
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Get HubSpot API key from environment
HUBSPOT_API_KEY = os.getenv("HUB_API_KEY")

class HubSpotClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.hubapi.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_contact_by_email(self, email):
        """Get contact information by email address"""
        url = f"{self.base_url}/crm/v3/objects/contacts"
        params = {
            "filter": f"email={email}",
            "properties": "last_platform_activity_date"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results") and len(data["results"]) > 0:
                contact = data["results"][0]
                return contact.get("properties", {}).get("last_platform_activity_date")
            else:
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {email}: {str(e)}")
            return None

def enrich_csv_with_hubspot_data(input_file, output_file):
    """Add HubSpot last_platform_activity_date to CSV file"""
    
    if not HUBSPOT_API_KEY:
        print("Error: HUBSPOT_API_KEY not found in environment variables")
        print("Please set HUBSPOT_API_KEY in your .env file")
        return
    
    # Read the CSV file
    print(f"Reading {input_file}...")
    df = pd.read_csv(input_file)
    
    if 'email' not in df.columns:
        print("Error: 'email' column not found in CSV file")
        return
    
    # Initialize HubSpot client
    hubspot = HubSpotClient(HUBSPOT_API_KEY)
    
    # Add new column
    df['last_platform_activity_date'] = None
    
    # Process each email
    total_emails = len(df)
    for index, row in df.iterrows():
        email = row['email']
        print(f"Processing {index + 1}/{total_emails}: {email}")
        
        # Get HubSpot data
        last_activity = hubspot.get_contact_by_email(email)
        df.at[index, 'last_platform_activity_date'] = last_activity
        
        # Rate limiting - HubSpot allows 100 requests per 10 seconds
        if (index + 1) % 90 == 0:  # Leave some buffer
            print("Rate limiting - waiting 10 seconds...")
            time.sleep(10)
    
    # Save the enriched CSV
    print(f"Saving enriched data to {output_file}...")
    df.to_csv(output_file, index=False)
    print("Done!")

def main():
    input_file = "data/nytw-builders-with-agents.csv"
    output_file = "data/nytw-builders-with-agents-enriched.csv"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        sys.exit(1)
    
    enrich_csv_with_hubspot_data(input_file, output_file)

if __name__ == "__main__":
    main() 