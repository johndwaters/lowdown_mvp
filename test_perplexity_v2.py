#!/usr/bin/env python3
"""
Test script to verify Perplexity API connection with newer model names.
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
    
    # Try newer model names based on 2024/2025 updates
    models_to_test = [
        "sonar",
        "sonar-pro", 
        "sonar-reasoning",
        "llama-3.1-sonar-huge-128k-online",
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-instruct",
        "llama-3.1-8b-instruct",
        "mixtral-8x7b-instruct"
    ]
    
    print(f"🔑 Testing API key: {api_key[:15]}...")
    
    for model in models_to_test:
        print(f"\n🔍 Testing model: {model}")
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": "What is the F-35 Lightning II? Give a brief answer."
                }
            ],
            "max_tokens": 100,
            "temperature": 0.2
        }
        
        try:
            response = requests.post(base_url, headers=headers, json=payload, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                print(f"✅ SUCCESS with {model}")
                print(f"Response: {content[:150]}...")
                return model  # Return the first working model
            else:
                try:
                    error_data = response.json()
                    print(f"❌ FAILED with {model}")
                    print(f"Error: {error_data}")
                except:
                    print(f"❌ FAILED with {model}: {response.text}")
                
        except Exception as e:
            print(f"❌ EXCEPTION with {model}: {str(e)}")
    
    print("\n❌ No working models found")
    
    # Test if API key is valid by making a simple request
    print("\n🔍 Testing API key validity...")
    try:
        test_payload = {
            "model": "llama-3.1-8b-instruct",  # Try a basic model
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }
        response = requests.post(base_url, headers=headers, json=test_payload, timeout=10)
        print(f"API Key test status: {response.status_code}")
        if response.content:
            try:
                error_data = response.json()
                print(f"API Key test response: {error_data}")
            except:
                print(f"API Key test response: {response.text}")
    except Exception as e:
        print(f"API Key test exception: {str(e)}")
    
    return None

if __name__ == "__main__":
    print("🚀 Testing Perplexity API connection with newer models...")
    working_model = test_perplexity_api()
    
    if working_model:
        print(f"\n🎉 Found working model: {working_model}")
    else:
        print("\n💥 No working models found. API key might be invalid or expired.")
