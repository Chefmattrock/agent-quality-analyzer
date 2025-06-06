import sqlite3
conn = sqlite3.connect('data/agents.db')
cursor = conn.cursor()

# Get Grant Program Builder agents with reviews
cursor.execute("""
    SELECT COUNT(*) as total_agents,
           COUNT(CASE WHEN reviews_count > 0 THEN 1 END) as agents_with_reviews,
           SUM(CASE WHEN reviews_count > 0 THEN reviews_score * reviews_count ELSE 0 END) as weighted_ratings,
           SUM(CASE WHEN reviews_count > 0 THEN reviews_count ELSE 0 END) as total_reviews
    FROM agents 
    WHERE builder_grant_program = 1
""")

result = cursor.fetchone()
total_agents, agents_with_reviews, weighted_ratings, total_reviews = result

print(f"CORRECTED Grant Program Builder Review Analysis:")
print(f"Total agents: {total_agents}")
print(f"Agents with reviews: {agents_with_reviews}")
print(f"Agents without reviews: {total_agents - agents_with_reviews}")

if agents_with_reviews > 0:
    corrected_avg = weighted_ratings / total_reviews
    print(f"Corrected average rating (only reviewed agents): {corrected_avg:.2f}")
    print(f"Review coverage: {(agents_with_reviews/total_agents)*100:.1f}%")
else:
    print("No agents have reviews")

conn.close() 