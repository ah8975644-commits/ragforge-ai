import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from .env
api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OPENROUTER_MODEL")

if not api_key:
    print("❌ ERROR: OPENROUTER_API_KEY not found in .env file")
    print("   Please add your key to backend/.env")
    exit(1)

print(f"✅ API Key loaded")
print(f"✅ Model: {model}")
print("-" * 50)

# Simple test request to OpenRouter
url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

data = {
    "model": model,
    "messages": [
        {
            "role": "user",
            "content": "Say 'Hello from RAGForge AI!' in one sentence only."
        }
    ],
    "max_tokens": 50,
}

print("📤 Sending request to OpenRouter...")

try:
    response = requests.post(url, headers=headers, json=data, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        answer = result["choices"][0]["message"]["content"]
        print(f"✅ SUCCESS! Response received:")
        print(f"\n{answer}\n")
    else:
        print(f"❌ ERROR: Status code {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    print("   Check your internet connection and API key")