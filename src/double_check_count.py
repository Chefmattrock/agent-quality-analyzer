import sqlite3

conn = sqlite3.connect('data/agents.db')
cursor = conn.cursor()

# Check current count of Grant Program Builder agents
cursor.execute("SELECT COUNT(*) FROM agents WHERE builder_grant_program = 1")
current_count = cursor.fetchone()[0]

# Check how many contacts are in the Grant Program Builders
cursor.execute("""
    SELECT COUNT(DISTINCT json_extract(authors, '$')) 
    FROM agents 
    WHERE builder_grant_program = 1 
    AND json_extract(authors, '$') IS NOT NULL
""")

print(f"Current Grant Program Builder agents in database: {current_count}")
print(f"Files show 158 agents (both original and fixed versions)")
print(f"\nPossible explanations for 164 → 158 discrepancy:")
print("1. Previous count was from a different analysis or dataset")
print("2. Some agents were deleted from the database between runs")
print("3. Some Grant Program Builders were removed from HubSpot list 301")
print("4. Different filtering was applied in previous analysis")

conn.close() 