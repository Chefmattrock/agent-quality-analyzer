#!/usr/bin/env python3
"""
Fix the outreach_builders.csv file with proper email addresses.
Based on the attached data from the conversation.
"""

import pandas as pd
import csv

# Data from the attached file
correct_data = [
    ["6619b6e922524415b42a5b96ef4dd320", "Chris Shuptrine", "cshuptrine", "chris.shuptrine@gmail.com"],
    ["4dc11027776d484c92b6b13cd3a1013c", "Dominik Sigmund", "DominikSigmund", "sigmund.dominik@googlemail.com"],
    ["cbd505fdf0964b5c", "", "SurajKripalani", "suraj.kripalani@bonbillo.com"],
    ["493373b53fda4d12", "Nishith", "nhs4you", "nhs4ai@gmail.com"],
    ["bc338ed620ef4638bc6c5a9c725f80e0", "Jeff Ocaya", "jeffocaya", "hijeffocaya@gmail.com"],
    ["4c60aa833303457a", "Enrich Labs", "", "team@enrich.so"],
    ["18e877934c414317", "Lee H", "Bellcurvellc", ""],
    ["68a7d7ebe431418bb8e8c22963cd7c56", "Meghan O'Keefe", "", "meglizokeefe@gmail.com"],
    ["fcc120e3cab948c6", "VAMSHI REDDY", "", "vamshi@chain8.org"],
    ["98d8f13f37144549", "Christopher Kiper", "", "chriskiper@gmail.com"],
    ["$device:19552f33e11bce-06ca8fc100198f-b457453-46500-19552f33e11bce", "Ashna Thakkar", "thakkar_ashna", "ashna.thakkar@bonbillo.com"],
    ["58ea52ad3b2a4df6", "", "uussamaab", ""],
    ["0558ee5500dc458784239019d6e77f51", "Brandon Smith", "bizae21", "smithbrandonarthur@gmail.com"],
    ["a646e3d230264200", "William Mulcahy", "AiCausal", "willjoemo@gmail.com"],
    ["c87c458d52754180", "Rick Flores", "rickflores305", "rickflores305@gmail.com"],
    ["18b51e30a5074e93", "Dhruv Atreja", "DhruvAtreja1", "dhruvatrejamain@gmail.com"],
    ["b36efea733894a6e", "Clint Fontanella", "", "clinttfontanella@gmail.com"],
    ["e55c3645ebe9487b", "Nishit Maheta", "nishitmaheta", "nvmaheta.mca@gmail.com"]
]

def fix_outreach_csv():
    # Read the current CSV to get all the other data
    print("Reading current outreach_builders.csv...")
    
    # Try multiple parsing methods
    df = None
    try:
        df = pd.read_csv("data/outreach_builders.csv", quotechar='"')
    except:
        try:
            # Try with csv module
            rows = []
            with open("data/outreach_builders.csv", 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rows.append(row)
            df = pd.DataFrame(rows)
        except Exception as e:
            print(f"Failed to read CSV: {e}")
            return False
    
    print(f"Loaded {len(df)} rows")
    
    # Create email mapping
    email_mapping = {}
    for user_token, name, twitter, email in correct_data:
        email_mapping[user_token] = email
    
    # Update email column
    for index, row in df.iterrows():
        user_token = row['user_token']
        if user_token in email_mapping:
            df.at[index, 'email'] = email_mapping[user_token]
            print(f"Updated email for {user_token}: {email_mapping[user_token]}")
    
    # Save the corrected file
    print("Saving corrected file...")
    df.to_csv("data/outreach_builders_fixed.csv", index=False, quoting=csv.QUOTE_ALL)
    print("Saved as data/outreach_builders_fixed.csv")
    
    # Show summary
    valid_emails = df[df['email'].notna() & (df['email'] != '') & (df['email'] != 'nan')]
    print(f"Total rows: {len(df)}")
    print(f"Rows with valid emails: {len(valid_emails)}")
    
    return True

if __name__ == "__main__":
    fix_outreach_csv() 