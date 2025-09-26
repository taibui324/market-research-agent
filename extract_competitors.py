#!/usr/bin/env python3
import json

# Read the JSON file
with open('/Users/mac/Desktop/ai-challenge-market-research/research_state_grounding_logs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract competitors data
competitors_data = {}

# Check for competitors in the main structure
if "competitors" in data:
    competitors_data = data["competitors"]

print("=== COMPETITORS FOUND ===")
for company_name, competitor_info in competitors_data.items():
    print(f"\nCompany: {company_name}")
    print(f"URL: {competitor_info.get('company_url', 'N/A')}")
    print(f"Location: {competitor_info.get('hq_location', 'N/A')}")
    print(f"Industry: {competitor_info.get('industry', 'N/A')}")
    
    # Extract organized content
    if "site_scrape" in competitor_info and "organized_content" in competitor_info["site_scrape"]:
        organized_content = competitor_info["site_scrape"]["organized_content"]
        print(f"\nOrganized Content Categories:")
        
        for category, category_data in organized_content.items():
            print(f"\n  📁 {category}:")
            if isinstance(category_data, dict) and "content" in category_data:
                content_items = category_data["content"]
                print(f"    Total items: {len(content_items)}")
                
                # Show first few items
                for i, item in enumerate(content_items[:3]):
                    title = item.get("title", "No title")
                    url = item.get("url", "")
                    content_preview = item.get("content", "")[:100] + "..." if len(item.get("content", "")) > 100 else item.get("content", "")
                    print(f"    {i+1}. {title}")
                    print(f"       URL: {url}")
                    print(f"       Content: {content_preview}")
                
                if len(content_items) > 3:
                    print(f"    ... and {len(content_items) - 3} more items")
    else:
        print("  No organized content found")

print(f"\n=== SUMMARY ===")
print(f"Total competitors found: {len(competitors_data)}")
