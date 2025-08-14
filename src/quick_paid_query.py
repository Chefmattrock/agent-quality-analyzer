#!/usr/bin/env python3
import os
import sqlite3

# Connect to database
db_path = 'data/agents.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Count paid agents NOT in builder program
cursor.execute("SELECT COUNT(*) FROM agents WHERE price > 0 AND (builder_grant_program = 0 OR builder_grant_program IS NULL)")
paid_non_builder = cursor.fetchone()[0]

# Count total paid agents
cursor.execute("SELECT COUNT(*) FROM agents WHERE price > 0")
total_paid = cursor.fetchone()[0]

# Count paid builder agents  
cursor.execute("SELECT COUNT(*) FROM agents WHERE price > 0 AND builder_grant_program = 1")
paid_builder = cursor.fetchone()[0]

print(f"ANSWER: {paid_non_builder:,} paid agents are NOT in the builder program")
print(f"Total paid agents: {total_paid:,}")
print(f"Paid builder program agents: {paid_builder:,}")
print(f"Percentage of paid agents NOT in builder program: {(paid_non_builder/total_paid)*100:.1f}%")

conn.close() 