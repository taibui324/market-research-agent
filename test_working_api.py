#!/usr/bin/env python3
"""
Original test_working_api.py - Manual HTTP requests version
This version uses direct HTTP requests without OpenAI SDK
"""
import os
import requests
import gzip
import json
from datetime import datetime

def test_working_api():
    """Test the AIG API using manual HTTP requests"""
    
    # Get environment variables
    api_key = os.getenv("AIG_API_KEY")
    base_url = os.getenv("AIG_BASE_URL", "https://api.aig.deca-dev.com/v1")
    organization_id = os.getenv("AIG_ORGANIZATION_ID", "01haxd218s50f6yy4jf2f92fzf")
    aig_profile_id = os.getenv("AIG_PROFILE_ID", "x-ai:grok-4-0709")
    model_id = os.getenv("AIG_MODEL_ID", "x-ai:grok-4-0709")
    
    if not api_key:
        print("❌ Error: AIG_API_KEY environment variable is required")
        return False
    
    print("🔧 Configuration:")
    print(f"   Base URL: {base_url}")
    print(f"   API Key: {api_key[:20]}...")
    print(f"   Organization ID: {organization_id}")
    print(f"   Profile ID: {aig_profile_id}")
    print(f"   Model ID: {model_id}")
    print()
    
    # Prepare the request
    url = f"{base_url}/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Authorization": f"Bearer {api_key}",
        "x-api-key": api_key,
        "x-aig-organization-id": organization_id,
        "x-aig-profile": aig_profile_id,
        "x-service-id": "ai-challenge"
    }
    
    # Test message for customer mapping
    message_content = """
Analyze consumer needs mapping and market trends for the Food & Beverage industry.

Analysis Period: 2025-03-29 to 2025-09-27 (Last 6 months)

Provide a comprehensive analysis including:

1. **Consumer Insights**: Identify key consumer behavior clusters with specific needs/trends, frequency counts (number of posts/mentions), and key insights.

2. **Trend Summaries**: Break down the 6-month period into monthly or bi-monthly trend summaries showing how consumer behavior evolved.

3. **Industry Focus**: Analyze the Food & Beverage industry specifically without focusing on any particular company.

Requirements:
- For consumer insights: Provide cluster categories (Quality, Convenience, Price, Sustainability, Digital, etc.)
- For frequency: Provide actual numbers of posts/mentions found
- For trend summaries: Include specific date ranges and behavioral changes
- Focus on demographic and psychographic trends
- Include emerging consumer needs and pain points
- Provide market-level insights from industry sources and social feedback

Generate structured data that covers the entire analysis period from 2025-03-29 to 2025-09-27.
"""
    
    payload = {
        "model": model_id,
        "messages": [
            {
                "role": "user",
                "content": message_content
            }
        ],
        "temperature": 0.7,
        "max_tokens": 4000,
        "search_parameters": {
            "mode": "on"
        }
    }
    
    print("🚀 Making API request...")
    print(f"   URL: {url}")
    print(f"   Model: {model_id}")
    print(f"   Message length: {len(message_content)} characters")
    print()
    
    try:
        # Make the request
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        print()
        
        if response.status_code != 200:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        # Handle gzipped response if needed
        content = response.content
        if response.headers.get('content-encoding') == 'gzip':
            print("🗜️  Decompressing gzipped response...")
            content = gzip.decompress(content)
        
        # Parse JSON response
        try:
            result = json.loads(content.decode('utf-8'))
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"   Raw content: {content[:500]}...")
            return False
        
        print("✅ API request successful!")
        print()
        
        # Display response details
        if 'choices' in result and result['choices']:
            choice = result['choices'][0]
            message = choice.get('message', {})
            content = message.get('content', '')
            
            print("📝 Response Content:")
            print(f"   Content length: {len(content)} characters")
            print(f"   Finish reason: {choice.get('finish_reason')}")
            print()
            
            # Show first 500 characters of content
            print("📄 Content Preview:")
            print("-" * 60)
            print(content[:500])
            if len(content) > 500:
                print("...")
            print("-" * 60)
            print()
        
        # Display usage information
        if 'usage' in result:
            usage = result['usage']
            print("📊 Token Usage:")
            print(f"   Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
            print(f"   Completion tokens: {usage.get('completion_tokens', 'N/A')}")
            print(f"   Total tokens: {usage.get('total_tokens', 'N/A')}")
            print()
        
        # Display citations if available
        if 'citations' in result:
            citations = result['citations']
            print(f"🔗 Citations: {len(citations)} found")
            for i, citation in enumerate(citations[:3], 1):
                print(f"   {i}. {citation.get('title', 'No title')}")
                print(f"      URL: {citation.get('url', 'No URL')}")
            print()
        
        # Save full response to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"api_test_response_{timestamp}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"💾 Full response saved to: {output_file}")
        except Exception as e:
            print(f"⚠️  Could not save response to file: {e}")
        
        return True
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 60 seconds")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🧪 AIG API Test - Manual HTTP Requests Version")
    print("=" * 60)
    print()
    
    # Check environment variables
    required_vars = ["AIG_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print()
        print("Usage: AIG_BASE_URL=https://api.aig.deca-dev.com/v1 AIG_API_KEY=your_key python test_working_api.py")
        return False
    
    # Run the test
    success = test_working_api()
    
    print()
    print("=" * 60)
    if success:
        print("🎉 API test completed successfully!")
        return True
    else:
        print("❌ API test failed!")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
