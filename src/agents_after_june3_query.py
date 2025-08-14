#!/usr/bin/env python3
"""
Query to find agents created after June 3rd.
Usage: python agents_after_june3_query.py [year] [--csv output.csv]
"""

import sqlite3
import sys
import argparse
import csv
from datetime import datetime

def query_agents_after_june3(year=2024, csv_output=None):
    """
    Find all agents created after June 3rd of the specified year.
    
    Args:
        year (int): The year to check (default: 2024)
        csv_output (str): Optional CSV file to save results
    """
    
    # Connect to database
    db_path = 'data/agents.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Query for agents created after June 3rd
    cutoff_date = f"{year}-06-03 00:00:00"
    
    query = """
    SELECT 
        agent_id,
        agent_id_human,
        name,
        description,
        created_at,
        status,
        type,
        price,
        executions,
        reviews_count,
        reviews_score
    FROM agents 
    WHERE created_at > ? 
    ORDER BY created_at DESC
    """
    
    c.execute(query, (cutoff_date,))
    results = c.fetchall()
    
    # Get column names
    columns = [description[0] for description in c.description]
    
    conn.close()
    
    print(f"\n🔍 Agents created after June 3rd, {year}")
    print(f"{'='*60}")
    print(f"Found {len(results)} agents")
    print(f"{'='*60}")
    
    if results:
        # Print first few results as preview
        print("\nFirst 10 results:")
        for i, row in enumerate(results[:10]):
            agent_id, agent_id_human, name, description, created_at, status, agent_type, price, executions, reviews_count, reviews_score = row
            print(f"\n{i+1}. {name} ({agent_id_human})")
            print(f"   Created: {created_at}")
            print(f"   Status: {status} | Type: {agent_type} | Price: ${price}")
            print(f"   Executions: {executions} | Reviews: {reviews_count} (score: {reviews_score})")
            if description:
                desc_preview = description[:100] + "..." if len(description) > 100 else description
                print(f"   Description: {desc_preview}")
        
        if len(results) > 10:
            print(f"\n... and {len(results) - 10} more agents")
        
        # Save to CSV if requested
        if csv_output:
            with open(csv_output, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(columns)
                writer.writerows(results)
            print(f"\n📄 Results saved to: {csv_output}")
    
    else:
        print(f"No agents found created after June 3rd, {year}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Find agents created after June 3rd')
    parser.add_argument('year', nargs='?', type=int, default=2024, 
                       help='Year to check (default: 2024)')
    parser.add_argument('--csv', help='Save results to CSV file')
    
    args = parser.parse_args()
    
    try:
        results = query_agents_after_june3(args.year, args.csv)
        
        # Summary statistics
        if results:
            total_executions = sum(row[8] or 0 for row in results)  # executions column
            total_reviews = sum(row[9] or 0 for row in results)    # reviews_count column
            avg_price = sum(row[7] or 0 for row in results) / len(results)  # price column
            
            print(f"\n📊 Summary Statistics:")
            print(f"   Total agents: {len(results)}")
            print(f"   Total executions: {total_executions:,}")
            print(f"   Total reviews: {total_reviews:,}")
            print(f"   Average price: ${avg_price:.2f}")
            
            # Date range
            earliest = min(row[4] for row in results if row[4])  # created_at column
            latest = max(row[4] for row in results if row[4])
            print(f"   Date range: {earliest} to {latest}")
        
    except FileNotFoundError:
        print("Error: agents.db not found. Please run pull_public_agents.py first.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 