#!/usr/bin/env python3
"""
Test script to verify Perplexity API connection and find correct model names.
"""
import requests
import json
import os

def test_perplexity_api():
    api_key = "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"
    base_url = "https://api.perplexity.ai/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Try different model names
    models_to_test = [
        "llama-3.1-sonar-small-128k-online",
        "llama-3.1-sonar-large-128k-online", 
        "sonar-small-online",
        "sonar-medium-online",
        "sonar-large-online",
        "llama-3.1-sonar-small-128k-chat",
        "llama-3.1-sonar-large-128k-chat"
    ]
    
    for model in models_to_test:
        print(f"\n🔍 Testing model: {model}")
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": "What is the F-35 Lightning II?"
                }
            ],
            "max_tokens": 100,
            "temperature": 0.2
        }
        
        try:
            response = requests.post(base_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                print(f"✅ SUCCESS with {model}")
                print(f"Response: {content[:100]}...")
                return model  # Return the first working model
            else:
                error_data = response.json() if response.content else {"error": "No content"}
                print(f"❌ FAILED with {model}: {response.status_code}")
                print(f"Error: {error_data}")
                
        except Exception as e:
            print(f"❌ EXCEPTION with {model}: {str(e)}")
    
    print("\n❌ No working models found")
    return None

if __name__ == "__main__":
    print("🚀 Testing Perplexity API connection...")
    working_model = test_perplexity_api()
    
    if working_model:
        print(f"\n🎉 Found working model: {working_model}")
    else:
        print("\n💥 No working models found. Check API key or model availability.")
