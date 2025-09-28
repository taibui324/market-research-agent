#!/usr/bin/env python3
"""
Correct parser for competitors' organized content from research_state_grounding_logs.json
"""

import json
import sys

def parse_competitors_organized_content():
    """Parse competitors' organized content from the research state grounding logs."""
    
    # Read the JSON file
    with open('/Users/mac/Desktop/ai-challenge-market-research/research_state_grounding_logs.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract competitors data from the main "competitors" key
    competitors_data = data.get("competitors", {})
    
    print("=== COMPETITORS ORGANIZED CONTENT ===")
    print(f"Found {len(competitors_data)} competitors\n")
    
    parsed_competitors = {}
    
    for company_name, competitor_info in competitors_data.items():
        print(f"🏢 {company_name}")
        print("-" * 50)
        
        # Basic company info
        print(f"📍 Location: {competitor_info.get('hq_location', 'N/A')}")
        print(f"🌐 Website: {competitor_info.get('company_url', 'N/A')}")
        print(f"🏭 Industry: {competitor_info.get('industry', 'N/A')}")
        
        # Extract organized content
        organized_content = {}
        if "site_scrape" in competitor_info and "organized_content" in competitor_info["site_scrape"]:
            organized_content = competitor_info["site_scrape"]["organized_content"]
            
            print(f"\n📊 Content Categories:")
            for category, category_data in organized_content.items():
                print(f"\n  📁 {category}:")
                
                if isinstance(category_data, dict) and "content" in category_data:
                    content_items = category_data["content"]
                    print(f"    Total items: {len(content_items)}")
                    
                    # Show first few items with details
                    for i, item in enumerate(content_items[:5]):  # Show first 5 items
                        title = item.get("title", "No title")
                        url = item.get("url", "")
                        content_preview = item.get("content", "")
                        
                        # Truncate content for display
                        if len(content_preview) > 200:
                            content_preview = content_preview[:200] + "..."
                        
                        print(f"    {i+1}. {title}")
                        print(f"       URL: {url}")
                        print(f"       Content: {content_preview}")
                        print()
                    
                    if len(content_items) > 5:
                        print(f"    ... and {len(content_items) - 5} more items")
                    
                    # Store parsed content
                    organized_content[category] = {
                        "content": content_items,
                        "total_items": len(content_items)
                    }
        else:
            print("  No organized content found")
        
        # Store parsed competitor data
        parsed_competitors[company_name] = {
            "company_info": {
                "company": competitor_info.get("company", company_name),
                "company_url": competitor_info.get("company_url", ""),
                "hq_location": competitor_info.get("hq_location", ""),
                "industry": competitor_info.get("industry", "Unknown")
            },
            "organized_content": organized_content
        }
        
        print("\n" + "="*80 + "\n")
    
    return parsed_competitors

def create_swot_competitors_data(parsed_competitors):
    """Create formatted competitors data for SWOT analysis."""
    
    swot_data = "=== COMPETITORS ANALYSIS FOR SWOT ===\n\n"
    
    for company_name, data in parsed_competitors.items():
        company_info = data["company_info"]
        organized_content = data["organized_content"]
        
        swot_data += f"COMPETITOR: {company_name}\n"
        swot_data += f"Location: {company_info['hq_location']}\n"
        swot_data += f"Website: {company_info['company_url']}\n"
        swot_data += f"Industry: {company_info['industry']}\n\n"
        
        if organized_content:
            swot_data += "Key Content Areas:\n"
            for category, category_data in organized_content.items():
                if isinstance(category_data, dict) and "content" in category_data:
                    content_items = category_data["content"]
                    swot_data += f"\n- {category.upper()} ({len(content_items)} items):\n"
                    
                    # Add sample content titles and key info
                    for item in content_items[:10]:  # First 10 items
                        title = item.get("title", "No title")
                        url = item.get("url", "")
                        content = item.get("content", "")
                        
                        if title and title != "No title":
                            swot_data += f"  • {title}\n"
                        
                        # Add key content snippets (first 100 chars)
                        if content:
                            content_snippet = content[:100].replace('\n', ' ').strip()
                            if content_snippet:
                                swot_data += f"    {content_snippet}...\n"
        
        swot_data += "\n" + "-"*60 + "\n\n"
    
    return swot_data

def main():
    """Main function to parse and display competitors' organized content."""
    
    print("Parsing competitors' organized content from research state grounding logs...")
    
    # Parse the content
    parsed_competitors = parse_competitors_organized_content()
    
    if not parsed_competitors:
        print("No competitors data found in the file.")
        return
    
    # Create SWOT-ready format
    print("\n" + "="*80)
    print("COMPETITORS DATA FOR SWOT ANALYSIS")
    print("="*80)
    
    swot_competitors_data = create_swot_competitors_data(parsed_competitors)
    print(swot_competitors_data)
    
    # Save parsed data to JSON file
    output_file = "/Users/mac/Desktop/ai-challenge-market-research/competitors_parsed.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(parsed_competitors, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Parsed data saved to: {output_file}")
    
    # Save SWOT-ready format
    swot_output_file = "/Users/mac/Desktop/ai-challenge-market-research/competitors_for_swot.txt"
    with open(swot_output_file, 'w', encoding='utf-8') as f:
        f.write(swot_competitors_data)
    
    print(f"✅ SWOT-ready format saved to: {swot_output_file}")
    
    # Also create a simple summary for the SWOT analysis node
    summary = f"Found {len(parsed_competitors)} competitors with organized content:\n"
    for company_name, data in parsed_competitors.items():
        organized_content = data["organized_content"]
        total_categories = len(organized_content)
        total_items = sum(cat_data.get("total_items", 0) for cat_data in organized_content.values() if isinstance(cat_data, dict))
        summary += f"- {company_name}: {total_categories} categories, {total_items} total content items\n"
    
    print(f"\n📋 SUMMARY:\n{summary}")

if __name__ == "__main__":
    main()
