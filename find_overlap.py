import csv

def read_emails_from_file(filename):
    emails = set()
    with open(filename, 'r') as f:
        if filename.endswith('.csv'):
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if len(row) > 0:
                    email = row[0].strip().lower() if filename == 'data/accounts-created-during-nytw.csv' else row[3].strip().lower()
                    if email and '@' in email:
                        emails.add(email)
        else:
            for line in f:
                email = line.strip().lower()
                if email and '@' in email:
                    emails.add(email)
    return emails

# Read emails from both files
accounts_emails = read_emails_from_file('data/accounts-created-during-nytw.csv')
hubspot_emails = read_emails_from_file('data/hubspot-crm-exports-nytw-approved-guests-2025-06-13.csv')

# Find overlap
overlap = accounts_emails.intersection(hubspot_emails)

# Print results
print(f"Number of emails in accounts-created-during-nytw.csv: {len(accounts_emails)}")
print(f"Number of emails in hubspot-crm-exports-nytw-approved-guests-2025-06-13.csv: {len(hubspot_emails)}")
print(f"Number of overlapping emails: {len(overlap)}")
print("\nOverlapping emails:")
for email in sorted(overlap):
    print(email) 