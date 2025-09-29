#!/usr/bin/env python3
"""
MVP Test for Curry Products - CustomerMappingResearcher
Run with: AIG_BASE_URL=https://api.aig.deca-dev.com/v1 AIG_API_KEY=your_key python test_curry_mvp.py
"""
import asyncio
import os
import sys
import json
from datetime import datetime, timedelta
from backend.nodes.researchers.customer_mapping import CustomerMappingResearcher


class MockWebSocketManager:
    """Mock WebSocket manager for testing"""
    
    async def send_status_update(self, job_id: str, status: str, message: str, result=None, error=None):
        print(f"📡 WebSocket Update - Job: {job_id}, Status: {status}")
        print(f"   Message: {message}")
        if result:
            print(f"   Result: {result}")
        if error:
            print(f"   Error: {error}")
        print()


async def test_curry_products_mvp():
    """MVP Test: CustomerMappingResearcher with packaged curry products industry"""
    
    print("🍛 MVP Test: Packaged Curry Products Industry Analysis")
    print("=" * 70)
    
    # Check environment variables
    aig_base_url = os.getenv('AIG_BASE_URL')
    aig_api_key = os.getenv('AIG_API_KEY')
    
    if not aig_base_url or not aig_api_key:
        print("❌ Error: Missing required environment variables")
        print("   Please set AIG_BASE_URL and AIG_API_KEY")
        return False
    
    print(f"🔧 Using AIG_BASE_URL: {aig_base_url}")
    print(f"🔧 Using AIG_API_KEY: {aig_api_key[:20]}...")
    print()
    
    try:
        # Initialize the researcher
        print("🚀 Initializing CustomerMappingResearcher...")
        researcher = CustomerMappingResearcher()
        print(f"✅ Researcher initialized: {researcher.analyst_type}")
        print()
        
        # Test with packaged curry products industry
        state = {
            "industry": "Packaged curry products (Curry roux & ready-to-eat/retort curry)",
            "websocket_manager": MockWebSocketManager(),
            "job_id": "curry_mvp_001"
        }
        
        print("🍛 Testing with Packaged Curry Products industry...")
        print("   Focus: Curry roux & ready-to-eat/retort curry products")
        print("   Analysis Period: Last 6 months (default)")
        print()
        
        # Execute research
        print("🔍 Executing customer mapping research...")
        result = await researcher.research_customer_mapping(state)
        
        # Validate basic structure
        print("📊 Analysis Results:")
        print(f"   Status: {result.get('status')}")
        print(f"   Analyst Type: {result.get('analyst_type')}")
        print(f"   Start Date: {result.get('start_date')}")
        print(f"   End Date: {result.get('end_date')}")
        print()
        
        if result.get("status") != "success":
            print(f"❌ Research failed with status: {result.get('status')}")
            if result.get("error"):
                print(f"   Error: {result.get('error')}")
            return False
        
        # Check industry-specific insights
        consumer_insights = result.get("consumer_insights", [])
        trend_summaries = result.get("trend_summaries", [])
        
        print("✅ Curry products analysis completed successfully!")
        print(f"📊 Consumer Insights: {len(consumer_insights)}")
        print(f"📊 Trend Summaries: {len(trend_summaries)}")
        print()
        
        # Display sample insights for curry products
        if consumer_insights:
            print("🔍 Consumer Insights for Curry Products:")
            print("-" * 50)
            for i, insight in enumerate(consumer_insights[:5]):  # Show first 5
                cluster = insight.get("cluster", "Unknown")
                need_trend = insight.get("consumer_need_trend", "No description")
                frequency = insight.get("frequency", 0)
                key_insights = insight.get("key_insights", "No insights")
                
                print(f"{i+1}. Cluster: {cluster}")
                print(f"   Trend: {need_trend}")
                print(f"   Frequency: {frequency} posts/mentions")
                print(f"   Insights: {key_insights}")
                print()
        
        if trend_summaries:
            print("📈 Trend Summaries for Curry Products:")
            print("-" * 50)
            for i, trend in enumerate(trend_summaries[:3]):  # Show first 3
                start_date = trend.get("start_date", "Unknown")
                end_date = trend.get("end_date", "Unknown")
                highlights = trend.get("trend_highlights", "No highlights")
                behavior_changes = trend.get("consumer_behavior_changes", "No changes noted")
                
                print(f"{i+1}. Period: {start_date} to {end_date}")
                print(f"   Highlights: {highlights}")
                print(f"   Behavior Changes: {behavior_changes}")
                print()
        
        # Check for curry-specific keywords in results
        result_text = json.dumps(result).lower()
        curry_keywords = ["curry", "convenience", "ready", "meal", "flavor", "spice", "cooking", "roux", "retort"]
        found_keywords = [kw for kw in curry_keywords if kw in result_text]
        
        if found_keywords:
            print(f"🎯 Industry-relevant keywords found: {', '.join(found_keywords)}")
        else:
            print("⚠️  Warning: No curry-specific keywords found in results")
        print()
        
        # Check demographic and market insights
        demographic_trends = result.get("demographic_trends")
        emerging_needs = result.get("emerging_needs")
        market_implications = result.get("market_implications")
        
        if demographic_trends:
            print("👥 Demographic Trends:")
            print(f"   {demographic_trends}")
            print()
        
        if emerging_needs:
            print("🚀 Emerging Needs:")
            print(f"   {emerging_needs}")
            print()
        
        if market_implications:
            print("💼 Market Implications:")
            print(f"   {market_implications}")
            print()
        
        # Save results for review
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"curry_mvp_results_{timestamp}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, default=str, ensure_ascii=False)
            print(f"💾 Full results saved to: {output_file}")
        except Exception as e:
            print(f"⚠️  Could not save results to file: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Curry products MVP test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main function for MVP test"""
    
    print("🧪 CustomerMappingResearcher - Curry Products MVP Test")
    print("=" * 70)
    print()
    
    # Check environment
    if not os.getenv('AIG_BASE_URL') or not os.getenv('AIG_API_KEY'):
        print("❌ Missing environment variables!")
        print("Usage: AIG_BASE_URL=https://api.aig.deca-dev.com/v1 AIG_API_KEY=your_key python test_curry_mvp.py")
        sys.exit(1)
    
    # Run the MVP test
    success = await test_curry_products_mvp()
    
    print()
    print("=" * 70)
    if success:
        print("🎉 MVP Test completed successfully!")
        print("✅ Curry products customer mapping is working correctly.")
        sys.exit(0)
    else:
        print("❌ MVP Test failed!")
        print("🔧 Check the error messages above for troubleshooting.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
