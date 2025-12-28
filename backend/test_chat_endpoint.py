"""
Simple test to verify chat endpoint is working
Run with: python test_chat_endpoint.py
"""
import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
PROJECT_ID = 4

def test_chat_endpoint():
    """Test the chat endpoint"""

    print("Testing chat endpoint...")
    print(f"URL: {BASE_URL}/chat/{PROJECT_ID}")

    payload = {
        "message": "hello"
    }

    print(f"\nSending request with payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(
            f"{BASE_URL}/chat/{PROJECT_ID}",
            json=payload,
            timeout=120  # 2 minutes timeout
        )

        print(f"\nResponse Status Code: {response.status_code}")

        if response.status_code == 200:
            print("✅ SUCCESS!")
            response_data = response.json()
            print(f"\nResponse Data:")
            print(json.dumps(response_data, indent=2, default=str))
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.Timeout:
        print("❌ Request timed out after 120 seconds")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the server. Is it running?")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_chat_endpoint()
