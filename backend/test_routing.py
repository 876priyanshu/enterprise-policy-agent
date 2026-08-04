import requests
import argparse
import sys

API_URL = "http://127.0.0.1:8000/api/policy/query"

test_queries = [
    {

        "intent": "Internal Docs",
        "question": "What is the company's hardware upgrade policy?"
    },
    {
        "intent": "Web Search (Direct)",
        "question": "What are the latest features in Python 3.13?"
    },
    {
        "intent": "Fallback (Internal -> Web)",
        "question": "Did our competitor Microsoft announce any new AI models this week?" 
    }
]

def run_tests(token: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    print("\nStarting Routing Tests...\n" + "-"*40)
    
    for test in test_queries:
        print(f"Testing Intent: {test['intent']}")
        print(f"Question: {test['question']}")
        
        try:
            response = requests.post(
                API_URL, 
                headers=headers, 
                json={"question": test["question"]}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f" Route Selected: {data.get('source')}")
                print(f" Answer: {data.get('answer')[:150]}...") 
            elif response.status_code == 401:
                print(" Error 401: Unauthorized. Your token is invalid or expired.")
                sys.exit(1) # Stop the script so you don't keep hitting the API with a bad token
            else:
                print(f" Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f" Connection Error: {e}")
            
        print("-" * 40)

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Test LLM Routing")
    parser.add_argument("--token", type=str, help="Your JWT Auth Token")
    
    args = parser.parse_args()
    
    # If token isn't provided as a command-line argument, prompt the user for it
    active_token = args.token
    if not active_token:
        try:
            # This will automatically strip out spaces, double quotes, and single quotes
            active_token = input("Paste your JWT for this session: ").strip().strip('"').strip("'")
        except KeyboardInterrupt:
            print("\nTest cancelled.")
            sys.exit(0)
            
    if not active_token:
        print("Error: No token provided.")
        sys.exit(1)
        
    run_tests(active_token)