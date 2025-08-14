import pandas as pd
import csv

def analyze_missing_emails():
    """
    Analyze the enhanced outreach list to identify builders missing email addresses.
    """
    # Read the enhanced outreach CSV
    df = pd.read_csv('data/enhanced_outreach_builders.csv')
    
    # Separate builders with and without emails
    builders_with_emails = df[df['email'].notna() & (df['email'] != '')]
    builders_without_emails = df[df['email'].isna() | (df['email'] == '')]
    
    print("=" * 80)
    print("EMAIL ADDRESS ANALYSIS FOR OUTREACH LIST")
    print("=" * 80)
    
    print(f"\n📧 BUILDERS WITH EMAIL ADDRESSES ({len(builders_with_emails)}):")
    print("-" * 50)
    for _, row in builders_with_emails.iterrows():
        print(f"✅ {row['name']} (@{row['twitter']})")
        print(f"   Email: {row['email']}")
        print(f"   Agents: {row['total_public_agents']}, Executions: {row['total_executions']}, Reviews: {row['total_reviews']}")
        if row['last_activity_date']:
            print(f"   Last Activity: {row['last_activity_date']}")
        print()
    
    print(f"\n❌ BUILDERS MISSING EMAIL ADDRESSES ({len(builders_without_emails)}):")
    print("-" * 50)
    
    # Sort by total executions to prioritize high-engagement builders
    builders_without_emails_sorted = builders_without_emails.sort_values('total_executions', ascending=False)
    
    for _, row in builders_without_emails_sorted.iterrows():
        print(f"❌ {row['name']} (@{row['twitter']})")
        print(f"   User Token: {row['user_token']}")
        print(f"   Agents: {row['total_public_agents']}, Executions: {row['total_executions']}, Reviews: {row['total_reviews']}")
        print(f"   Top Tags: {row['top_tags']}")
        print()
    
    # Summary statistics
    total_builders = len(df)
    email_coverage = len(builders_with_emails) / total_builders * 100
    
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Total builders in outreach list: {total_builders}")
    print(f"Builders with email addresses: {len(builders_with_emails)}")
    print(f"Builders missing email addresses: {len(builders_without_emails)}")
    print(f"Email coverage: {email_coverage:.1f}%")
    
    # Top priority builders for email discovery
    print(f"\n🎯 TOP PRIORITY FOR EMAIL DISCOVERY (by total executions):")
    print("-" * 50)
    top_5_missing = builders_without_emails_sorted.head(5)
    for i, (_, row) in enumerate(top_5_missing.iterrows(), 1):
        print(f"{i}. {row['name']} (@{row['twitter']})")
        print(f"   {row['total_executions']:,} total executions, {row['total_reviews']} reviews")
        print(f"   User Token: {row['user_token']}")
        print()

if __name__ == "__main__":
    analyze_missing_emails() 