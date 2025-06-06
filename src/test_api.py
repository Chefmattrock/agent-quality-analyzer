import os
import requests
import json
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
API_KEY = os.getenv("AGENT_AI_API_KEY")

def print_separator():
    print("\n" + "="*80 + "\n")

def test_api_endpoint():
    if not API_KEY:
        print("Error: API key not found. Please set AGENT_AI_API_KEY in your .env file")
        return

    url = "https://api.agent.ai/api/v2/agents/list"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    params = {
        "status": "public",
        "limit": 5
    }
    
    print_separator()
    print("REQUEST DETAILS:")
    print(f"URL: {url}")
    print(f"Headers: {json.dumps({k: v if k != 'Authorization' else '[REDACTED]' for k, v in headers.items()}, indent=2)}")
    print(f"Parameters: {json.dumps(params, indent=2)}")
    print_separator()
    
    try:
        print("Sending request...")
        response = requests.post(url, headers=headers, json=params)
        
        print("RESPONSE DETAILS:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response.elapsed.total_seconds():.2f} seconds")
        print("\nResponse Headers:")
        for header, value in response.headers.items():
            print(f"{header}: {value}")
        
        print_separator()
        print("RESPONSE BODY:")
        
        try:
            response_data = response.json()
            print("\nParsed JSON Response:")
            print(json.dumps(response_data, indent=2))
            
            if isinstance(response_data, dict):
                print("\nResponse Structure Analysis:")
                for key, value in response_data.items():
                    if isinstance(value, list):
                        print(f"- {key}: List with {len(value)} items")
                    elif isinstance(value, dict):
                        print(f"- {key}: Dictionary with keys: {', '.join(value.keys())}")
                    else:
                        print(f"- {key}: {type(value).__name__}")
                
                if "agents" in response_data:
                    agents = response_data["agents"]
                    print(f"\nFound {len(agents)} agents in response")
                    for i, agent in enumerate(agents, 1):
                        print(f"\nAgent {i}:")
                        for key in ["id", "name", "description", "status"]:
                            if key in agent:
                                value = agent[key]
                                if key == "description" and value:
                                    value = value[:100] + "..." if len(value) > 100 else value
                                print(f"  {key}: {value}")
            
        except json.JSONDecodeError:
            print("Failed to parse JSON response. Raw response body:")
            print(response.text)
            
    except requests.exceptions.RequestException as e:
        print("\nREQUEST ERROR:")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        if isinstance(e, requests.exceptions.ConnectionError):
            print("Connection Error: Please check your internet connection and the API endpoint URL.")
        elif isinstance(e, requests.exceptions.Timeout):
            print("Timeout Error: The request took too long to complete.")
        elif isinstance(e, requests.exceptions.TooManyRedirects):
            print("Redirect Error: Too many redirects.")

if __name__ == "__main__":
    print(f"Starting API test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    test_api_endpoint()
    print_separator()
    print("Test completed.")