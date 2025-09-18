#!/usr/bin/env python3
"""
Simple DuckDB query interface for agent runs analysis
"""

import duckdb
import sys
import json
from datetime import datetime

def connect_db():
    """Connect to the DuckDB database"""
    db_path = 'data/agent_runs.duckdb'
    try:
        return duckdb.connect(db_path)
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def run_query(conn, query, description="Query"):
    """Run a query and display results"""
    try:
        print(f"\n🔍 {description}")
        print("-" * 50)
        
        start_time = datetime.now()
        result = conn.execute(query).fetchall()
        query_time = datetime.now() - start_time
        
        if not result:
            print("No results found.")
            return
        
        # Display results
        for row in result:
            print(row)
        
        print(f"\n⏱️  Query completed in {query_time.total_seconds():.3f} seconds")
        print(f"📊 Returned {len(result)} rows")
        
    except Exception as e:
        print(f"❌ Query error: {e}")

def main():
    """Main query interface"""
    print("🦆 DuckDB Agent Runs Query Interface")
    print("=" * 50)
    
    conn = connect_db()
    if not conn:
        sys.exit(1)
    
    # Predefined useful queries
    queries = {
        "1": {
            "description": "Top 10 agents by total runs",
            "query": """
                SELECT DISTINCT agent_id, name, total_runs_30d 
                FROM agent_runs 
                ORDER BY total_runs_30d DESC 
                LIMIT 10
            """
        },
        "2": {
            "description": "Agents with highest token usage",
            "query": """
                SELECT 
                    name,
                    json_extract(response, '$.step-2.metadata.usage.total_tokens') as tokens,
                    json_extract(response, '$.step-2.metadata.usage.prompt_tokens') as prompt_tokens,
                    json_extract(response, '$.step-2.metadata.usage.completion_tokens') as completion_tokens
                FROM agent_runs 
                WHERE json_extract(response, '$.step-2.metadata.usage.total_tokens') IS NOT NULL
                ORDER BY CAST(json_extract(response, '$.step-2.metadata.usage.total_tokens') AS INTEGER) DESC
                LIMIT 10
            """
        },
        "3": {
            "description": "Engine usage statistics",
            "query": """
                SELECT 
                    json_extract(response, '$.step-2.engine') as engine,
                    COUNT(*) as usage_count
                FROM agent_runs 
                WHERE json_extract(response, '$.step-2.engine') IS NOT NULL
                GROUP BY json_extract(response, '$.step-2.engine')
                ORDER BY usage_count DESC
            """
        },
        "4": {
            "description": "Execution time analysis (longest running)",
            "query": """
                SELECT 
                    name,
                    run_started_at,
                    run_completed_at,
                    EXTRACT(EPOCH FROM (run_completed_at - run_started_at)) as duration_seconds,
                    total_steps
                FROM agent_runs 
                WHERE run_completed_at IS NOT NULL 
                    AND run_started_at IS NOT NULL
                    AND EXTRACT(EPOCH FROM (run_completed_at - run_started_at)) > 0
                ORDER BY duration_seconds DESC
                LIMIT 10
            """
        },
        "5": {
            "description": "Agents by total steps (most complex workflows)",
            "query": """
                SELECT DISTINCT 
                    name, 
                    total_steps,
                    total_runs_30d
                FROM agent_runs 
                ORDER BY total_steps DESC 
                LIMIT 10
            """
        },
        "6": {
            "description": "Recent runs (last 24 hours)",
            "query": """
                SELECT 
                    name,
                    run_started_at,
                    total_steps,
                    json_extract(response, '$.step-2.engine') as main_engine
                FROM agent_runs 
                WHERE run_started_at > (CURRENT_TIMESTAMP - INTERVAL 1 DAY)
                ORDER BY run_started_at DESC
                LIMIT 10
            """
        }
    }
    
    if len(sys.argv) > 1:
        # Run specific query number from command line
        query_num = sys.argv[1]
        if query_num in queries:
            query_info = queries[query_num]
            run_query(conn, query_info["query"], query_info["description"])
        else:
            print(f"❌ Query number '{query_num}' not found")
    else:
        # Interactive mode
        print("\nAvailable queries:")
        for num, info in queries.items():
            print(f"  {num}. {info['description']}")
        
        print("\nUsage:")
        print("  python query_duckdb.py [query_number]")
        print("  Example: python query_duckdb.py 1")
        
        print("\n💡 Or run custom queries:")
        print("  python -c \"import duckdb; conn=duckdb.connect('data/agent_runs.duckdb'); print(conn.execute('YOUR_QUERY').fetchall())\"")
    
    conn.close()

if __name__ == "__main__":
    main()

