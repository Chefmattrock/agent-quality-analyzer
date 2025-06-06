#!/usr/bin/env python3
import pandas as pd
import sqlite3

# Load paid traffic agents
paid_traffic_df = pd.read_csv('paid_traffic_exclusion_list.csv')
paid_traffic_ids = set(paid_traffic_df['agent_id'].tolist())

# Connect to database
conn = sqlite3.connect('data/agents.db')
cursor = conn.cursor()

# Get builder grant program agent IDs
cursor.execute("SELECT agent_id FROM agents WHERE builder_grant_program = 1")
builder_ids = set([row[0] for row in cursor.fetchall()])

# Find overlap
paid_traffic_and_builder = paid_traffic_ids.intersection(builder_ids)
paid_traffic_not_builder = paid_traffic_ids - builder_ids

print(f"ANSWER: {len(paid_traffic_not_builder)} agents received paid traffic but are NOT in the builder program")
print(f"Total paid traffic agents: {len(paid_traffic_ids)}")
print(f"Paid traffic agents also in builder program: {len(paid_traffic_and_builder)}")
print(f"Percentage NOT in builder program: {(len(paid_traffic_not_builder)/len(paid_traffic_ids))*100:.1f}%")

conn.close() 