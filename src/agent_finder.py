import os
import requests
import json
import argparse
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv
from datetime import datetime
import sqlite3

# Load environment variables from .env file
project_root = os.path.dirname(os.path.dirname(__file__))
env_path = os.path.abspath(os.path.join(project_root, '.env'))
load_dotenv(dotenv_path=env_path, override=True)

# Get API key for Agent.ai V1 API from environment variables
API_KEY = os.getenv("AGENT_AI_API_KEY")

class AgentAIClient:
    def __init__(self, api_key: str):
        """
        Initialize the AgentAIClient with API key.
        
        Args:
            api_key (str): Your agent.ai API key
        """
        if not api_key:
            raise ValueError("API key is required. Please set AGENT_AI_API_KEY in your .env file")
            
        self.api_key = api_key
        self.base_url = "https://api-lr.agent.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def find_agents(
        self,
        status: str = "public",
        slug: Optional[str] = None,
        query: Optional[str] = None,
        tag: Optional[str] = None,
        intent: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Search and discover agents based on various criteria.
        
        Args:
            status (str): Agent status (e.g., "public")
            slug (str, optional): Agent slug/identifier
            query (str, optional): Search query
            tag (str, optional): Filter by tag (e.g., "Marketing", "Sales")
            intent (str, optional): User intent/use case
            limit (int): Number of results to return (max 100)
            offset (int): Number of results to skip
            
        Returns:
            tuple: (response_data, error_message)
            - response_data (dict): API response containing agent details if successful
            - error_message (str): Error message if request failed, None if successful
        """
        url = f"{self.base_url}/action/find_agents"
        
        # Build query parameters
        params = {
            "status": status,
            "limit": limit,
            "offset": offset
        }
        
        # Add optional parameters if provided
        if slug:
            params["slug"] = slug
        if query:
            params["query"] = query
        if tag:
            params["tag"] = tag
        if intent:
            params["intent"] = intent
            
        print(f"\nSending request with params: {json.dumps(params, indent=2)}")
        
        try:
            response = requests.post(url, headers=self.headers, json=params)
            
            # Check for HTTP errors
            if response.status_code == 401:
                return None, "Authentication failed. Please check your API key at https://agent.ai/user/settings#credits"
            elif response.status_code == 403:
                return None, "Access forbidden. Your API key may not have the required permissions."
            elif response.status_code == 404:
                return None, "Endpoint not found. Please check the API documentation."
            elif response.status_code == 429:
                return None, "Rate limit exceeded. Please try again later."
            elif response.status_code >= 500:
                return None, f"Server error (HTTP {response.status_code}). Please try again later."
            
            response.raise_for_status()
            return response.json(), None
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            if "ConnectionError" in str(e):
                error_msg += "\nPlease check your internet connection."
            elif "Timeout" in str(e):
                error_msg += "\nThe request timed out. Please try again."
            return None, error_msg

    def parse_agent_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse the API response into a more structured format.
        
        Args:
            response (dict): Raw API response
            
        Returns:
            list: List of parsed agent details
        """
        agents = []
        for agent in response.get("response", []):
            parsed_agent = {
                "id": agent.get("agent_id"),
                "human_id": agent.get("agent_id_human"),
                "name": agent.get("name"),
                "description": agent.get("description"),
                "status": agent.get("status"),
                "type": agent.get("type"),
                "price": agent.get("price"),
                "executions": agent.get("executions", 0),
                "reviews": {
                    "count": agent.get("reviews_count", 0),
                    "score": agent.get("reviews_score", 0)
                },
                "tags": agent.get("tags", []),
                "created_at": self._parse_timestamp(agent.get("created_at")),
                "updated_at": self._parse_timestamp(agent.get("updated_at")),
                "authors": self._parse_authors(agent.get("authors", {})),
                "approximate_time": agent.get("approximate_time"),
                "is_approved": agent.get("is_approved", False)
            }
            agents.append(parsed_agent)
        return agents

    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse timestamp string to datetime object."""
        if not timestamp_str:
            return None
        try:
            return datetime.strptime(timestamp_str, "%a, %d %b %Y %H:%M:%S %Z")
        except ValueError:
            return None

    def _parse_authors(self, authors: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse authors information."""
        return [
            {
                "user_token": user_token,
                "name": info.get("name"),
                "twitter_username": info.get("twitter_username"),
                "avatar": info.get("avatar")
            }
            for user_token, info in authors.items()
        ]

def initialize_agents_db(db_path='data/agents.db'):
    """
    Initialize the agents SQLite database and create the agents table if it doesn't exist.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            agent_id TEXT PRIMARY KEY,
            agent_id_human TEXT,
            approximate_time INTEGER,
            authors TEXT,
            created_at TEXT,
            description TEXT,
            executions INTEGER,
            featured_at TEXT,
            icon TEXT,
            invoke_agent_input TEXT,
            is_approved INTEGER,
            name TEXT,
            price REAL,
            reviews_count INTEGER,
            reviews_score REAL,
            status TEXT,
            tags TEXT,
            type TEXT,
            updated_at TEXT
        )
    ''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_agents_description ON agents(description)')
    conn.commit()
    conn.close()

def main():
    # Initialize the agents database
    initialize_agents_db()
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Search and discover agents from agent.ai',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-p', '--status', default='public', help='Agent status (e.g., "public")')
    parser.add_argument('-t', '--tag', help='Filter by tag (e.g., "Marketing", "Sales")')
    parser.add_argument('-n', '--limit', type=int, default=10, help='Number of results to return (max 100)')
    parser.add_argument('-o', '--offset', type=int, default=0, help='Number of results to skip')

    # If no arguments are provided, print help and exit
    import sys
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    args = parser.parse_args()
    
    try:
        client = AgentAIClient(API_KEY)
        
        # Search for agents with command line arguments
        response, error = client.find_agents(
            status=args.status,
            tag=args.tag,
            limit=args.limit,
            offset=args.offset
        )
        
        if error:
            print(f"\nError: {error}")
            return
            
        if response:
            print(f"\nRaw response length: {len(response.get('response', []))}")
            agents = client.parse_agent_response(response)
            print(f"Parsed {len(agents)} agents")
            
            # Insert agents into the database
            conn = sqlite3.connect('data/agents.db')
            c = conn.cursor()
            for agent in response.get('response', []):
                # Convert date fields to ISO 8601
                def to_iso8601(dt_str):
                    try:
                        dt = datetime.strptime(dt_str, "%a, %d %b %Y %H:%M:%S %Z")
                        return dt.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        return dt_str or None
                created_at = to_iso8601(agent.get('created_at'))
                updated_at = to_iso8601(agent.get('updated_at'))
                # Store lists/objects as JSON strings
                tags = json.dumps(agent.get('tags', []))
                invoke_agent_input = json.dumps(agent.get('invoke_agent_input', []))
                authors = json.dumps(agent.get('authors', {}))
                c.execute('''
                    INSERT OR REPLACE INTO agents (
                        agent_id, agent_id_human, approximate_time, authors, created_at, description, executions, featured_at, icon, invoke_agent_input, is_approved, name, price, reviews_count, reviews_score, status, tags, type, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    agent.get('agent_id'),
                    agent.get('agent_id_human'),
                    agent.get('approximate_time'),
                    authors,
                    created_at,
                    agent.get('description'),
                    agent.get('executions'),
                    agent.get('featured_at'),
                    agent.get('icon'),
                    invoke_agent_input,
                    int(agent.get('is_approved', False)),
                    agent.get('name'),
                    agent.get('price'),
                    agent.get('reviews_count'),
                    agent.get('reviews_score'),
                    agent.get('status'),
                    tags,
                    agent.get('type'),
                    updated_at
                ))
            conn.commit()
            conn.close()
            print(f"{len(agents)} agents found and added to the database.")
        else:
            print("No agents found in the response")
            
    except ValueError as e:
        print(f"\nConfiguration Error: {str(e)}")
    except Exception as e:
        print(f"\nUnexpected Error: {str(e)}")

if __name__ == "__main__":
    main()