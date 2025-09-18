# 🦆 DuckDB CLI Reference Guide

## Basic Usage

### Connect to Database
```zsh
# Interactive mode
duckdb data/agent_runs.duckdb

# Single command mode
duckdb data/agent_runs.duckdb -c "YOUR_SQL_QUERY"

# Read-only mode
duckdb data/agent_runs.duckdb -readonly
```

### Inside DuckDB CLI
```sql
-- Show all tables
SHOW TABLES;

-- Describe table structure
DESCRIBE agent_runs;

-- Exit DuckDB
.exit
-- or
.quit
```

## Essential CLI Commands

### 1. **Meta Commands (start with dot)**
```sql
.help                    -- Show help
.schema                  -- Show database schema
.tables                  -- List all tables
.mode                    -- Change output format
.timer on/off           -- Show query execution time
.width 20 30 40         -- Set column widths
```

### 2. **Output Formats**
```sql
.mode box               -- Nice ASCII boxes (default)
.mode csv               -- Comma-separated values
.mode json              -- JSON output
.mode markdown          -- Markdown table format
.mode table             -- Simple table format
```

### 3. **File Operations**
```sql
.output results.csv     -- Redirect output to file
.output                 -- Reset output to console
```

## Sample Queries for Your Data

### Basic Queries
```sql
-- Count all runs
SELECT COUNT(*) FROM agent_runs;

-- Top agents by runs
SELECT DISTINCT name, total_runs_30d 
FROM agent_runs 
ORDER BY total_runs_30d DESC 
LIMIT 10;

-- Recent runs
SELECT name, run_started_at, total_steps 
FROM agent_runs 
ORDER BY run_started_at DESC 
LIMIT 10;
```

### JSON Queries
```sql
-- Extract step engines
SELECT name, 
       json_extract(response, '$.step-1.engine') as step1_engine,
       json_extract(response, '$.step-2.engine') as step2_engine
FROM agent_runs 
LIMIT 5;

-- Token usage analysis
SELECT name,
       json_extract(response, '$.step-2.metadata.usage.total_tokens') as tokens
FROM agent_runs 
WHERE json_extract(response, '$.step-2.metadata.usage.total_tokens') IS NOT NULL
ORDER BY CAST(json_extract(response, '$.step-2.metadata.usage.total_tokens') AS INTEGER) DESC
LIMIT 10;

-- Engine usage statistics
SELECT json_extract(response, '$.step-2.engine') as engine,
       COUNT(*) as usage_count
FROM agent_runs 
WHERE json_extract(response, '$.step-2.engine') IS NOT NULL
GROUP BY json_extract(response, '$.step-2.engine')
ORDER BY usage_count DESC;
```

### Complex Queries
```sql
-- Execution time analysis
SELECT name,
       run_started_at,
       run_completed_at,
       EXTRACT(EPOCH FROM (run_completed_at - run_started_at)) as duration_seconds,
       total_steps
FROM agent_runs 
WHERE run_completed_at IS NOT NULL 
  AND run_started_at IS NOT NULL
  AND EXTRACT(EPOCH FROM (run_completed_at - run_started_at)) > 0
ORDER BY duration_seconds DESC
LIMIT 10;

-- Agent performance summary
SELECT name,
       COUNT(*) as total_runs,
       AVG(total_steps) as avg_steps,
       AVG(EXTRACT(EPOCH FROM (run_completed_at - run_started_at))) as avg_duration_seconds
FROM agent_runs 
WHERE run_completed_at IS NOT NULL 
  AND run_started_at IS NOT NULL
GROUP BY name
ORDER BY total_runs DESC
LIMIT 10;
```

## JSON Path Examples

Your `response` column contains nested JSON. Here are common paths:

```sql
-- Step information
json_extract(response, '$.step-1.engine')
json_extract(response, '$.step-2.metadata.usage.total_tokens')
json_extract(response, '$.step-3.response')

-- Nested arrays (use array index)
json_extract(response, '$.step-1.instructions[0].label')

-- Check if path exists
json_extract(response, '$.step-2.metadata') IS NOT NULL
```

## Performance Tips

1. **Use LIMIT** for exploration:
   ```sql
   SELECT * FROM agent_runs LIMIT 5;
   ```

2. **Filter before extracting JSON**:
   ```sql
   SELECT name, json_extract(response, '$.step-2.engine') 
   FROM agent_runs 
   WHERE response IS NOT NULL;
   ```

3. **Use DISTINCT for unique values**:
   ```sql
   SELECT DISTINCT json_extract(response, '$.step-2.engine') as engines
   FROM agent_runs;
   ```

## Quick Start Commands

```zsh
# Connect and explore
duckdb data/agent_runs.duckdb

# Inside DuckDB:
.timer on
SHOW TABLES;
DESCRIBE agent_runs;
SELECT COUNT(*) FROM agent_runs;

# Test JSON extraction
SELECT name, json_extract(response, '$.step-2.engine') 
FROM agent_runs 
LIMIT 5;

# Exit
.exit
```

## Export Results

```sql
-- Set CSV mode and export
.mode csv
.output top_agents.csv
SELECT DISTINCT name, total_runs_30d 
FROM agent_runs 
ORDER BY total_runs_30d DESC 
LIMIT 20;
.output

-- Back to box mode
.mode box
```

## Pro Tips

- **Tab completion**: Works for table names and column names
- **History**: Use ↑/↓ arrows to navigate command history  
- **Multi-line queries**: End with `;` to execute
- **Comments**: Use `--` for single line comments
- **Timing**: Use `.timer on` to see query performance

