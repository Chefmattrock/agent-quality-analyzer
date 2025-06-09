# Agent Quality Analyzer

A comprehensive analysis toolkit for examining agent performance, builder programs, and traffic attribution across different agent groups.

## Project Structure

```
agent_quality_analyzer/
├── src/                    # Source code and analysis scripts
├── data/                   # Data files (database, CSVs, results) - gitignored
├── docs/                   # Documentation
├── venv/                   # Python virtual environment - gitignored
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agent_quality_analyzer
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Create a `.env` file in the root directory with your API keys:
   ```
   HUB_API_KEY=your_hubspot_api_key_here
   AGENT_AI_API_KEY=your_agent_ai_api_key_here
   ```

## Key Analysis Scripts

### Grant Program Builders Analysis
- `src/grant_program_analysis.py` - Main analysis of Grant Program Builders (HubSpot list 301)
- `src/grant_program_analysis_fixed.py` - Fixed version with corrected review scoring (excludes 0-review agents)

### Traffic Analysis  
- `src/find_paid_traffic_agents.py` - Identifies agents that received paid traffic
- `src/paid_traffic_vs_builder_analysis.py` - Analyzes overlap between paid traffic and builder program

### Comparison Analysis
- `src/three_group_comparison.py` - Compares performance across different agent groups
- `src/public_builders_analysis.py` - Analyzes public agent builders (Group B)
- `src/group_c_analysis.py` - Analyzes high-performance agent builders (Group C)

### Utility Scripts
- `src/user_builds.py` - Look up agents by user token
- `src/pull_public_agents.py` - Find and analyze specific agents
- `src/refresh_data.py` - Refresh agent data from API

## Usage Examples

### Analyze Grant Program Builders
```bash
python src/grant_program_analysis_fixed.py
```

### Find agents with paid traffic
```bash  
python src/find_paid_traffic_agents.py
```

### Compare three agent groups
```bash
python src/three_group_comparison.py
```

### Look up agents by user
```bash
python src/user_builds.py -u <user_token>
```

## Data Files

All data files are stored in the `data/` directory and are excluded from git for privacy:

- `agents.db` - Main SQLite database with agent information
- Various CSV exports for analysis results
- Temporary analysis files and logs

## Important Notes

⚠️ **Privacy & Security**
- All API keys must be stored in `.env` file (not committed to git)
- Data files containing agent information are gitignored
- No sensitive tokens or keys should be hardcoded in scripts

⚠️ **Review Scoring Fix**
- Use `grant_program_analysis_fixed.py` for accurate review calculations
- This version excludes agents with 0 reviews from average calculations
- Original version incorrectly included 0-review agents as 0.0 ratings

## Contributing

When adding new scripts:
1. Place them in the `src/` directory
2. Add comprehensive docstrings explaining purpose and usage
3. Use environment variables for API keys
4. Export results to `data/` directory
5. Update README if adding significant functionality 