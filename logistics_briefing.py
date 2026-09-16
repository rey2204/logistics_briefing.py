import os
import requests
import boto3
from datetime import datetime

# Load credentials from GitHub 
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
SES_CLIENT = boto3.client("ses", region_name="us-east-2")

# List of target URLs
# List of target URLs for Global Logistics & Supply Chain
SOURCES = [
    {"name": "Peterson Institute (PIIE)", "url": "https://www.piie.com"},
    {"name": "Kiel Institute for the World Economy", "url": "https://www.ifw-kiel.de"},
    {"name": "UN Trade and Development (UNCTAD)", "url": "https://unctad.org"},
    {"name": "Observatory of Economic Complexity (OEC)", "url": "https://oec.world"},
    {"name": "Drewry World Container Index", "url": "https://www.drewry.co.uk"},
    {"name": "Freightos Weekly Freight Update", "url": "https://www.freightos.com/freight-resources/the-weekly-freightos-freight-rate-update/"},
    {"name": "Flexport Freight Market Update", "url": "https://www.flexport.com/market-updates/"},
    {"name": "Xeneta", "url": "https://www.xeneta.com/blog"},
    {"name": "Alphaliner", "url": "https://www.alphaliner.com"},
    {"name": "Journal of Commerce (JOC)", "url": "https://www.joc.com"},
    {"name": "DAT Trendlines (North American Trucking)", "url": "https://www.dat.com/trendlines"},
    {"name": "FreightWaves", "url": "https://www.freightwaves.com"},
    {"name": "Cass Freight Index", "url": "https://www.cassinfo.com/freight-audit-payment/cass-transportation-indexes"},
    {"name": "WorldACD (Air Freight)", "url": "https://www.worldacd.com"},
    {"name": "TAC Index", "url": "https://tacindex.com"},
    {"name": "IATA Air Cargo Market Analysis", "url": "https://www.iata.org"},
    {"name": "Air Cargo News", "url": "https://www.aircargonews.net"},
    {"name": "National Bureau of Economic Research (NBER)", "url": "https://www.nber.org"},
    {"name": "Kearney Reshoring Index", "url": "https://www.kearney.com/service/operations-performance/us-reshoring-index"},
    {"name": "Reshoring Initiative", "url": "https://reshorenow.org/"},
    {"name": "S&P Global Market Intelligence", "url": "https://www.spglobal.com/market-intelligence/en/news-insights"},
    {"name": "ISM Report On Business", "url": "https://www.ismworld.org/supply-management-news-and-reports/reports/"},
    {"name": "Boston Consulting Group (BCG) Supply Chain", "url": "https://www.bcg.com/capabilities/operations/supply-chain-management"},
    {"name": "Gartner Supply Chain Practice", "url": "https://www.gartner.com/en/supply-chain"}
]

def main():
    collected_data = []
    print("Collecting publication data...")
    
    for source in SOURCES:
        print(f"Reading {source['name']}...")
        try:
            reader_url = f"https://r.jina.ai/{source['url']}"
            response = requests.get(reader_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            if response.status_code == 200:
                content = response.text[:4000]
                collected_data.append(f"### SOURCE: {source['name']} ({source['url']})\n{content}\n")
        except Exception as e:
            print(f"Failed to fetch {source['url']}: {e}")

    compiled_context = "\n".join(collected_data)

   prompt = f"""You are a global supply chain and logistics risk analyst. 
Based ONLY on the following source materials, synthesize this week's developments into an Axios-style briefing.

Formatting guidelines:
1. Lead with the single most critical structural or geopolitical trade disruption under a 'The Big Picture' section.
2. Follow with 3 to 5 key tactical developments using concise bullet points.
3. Organize the remaining analysis under targeted headers specifically designed to surface blind spots for teams managing:
   - Air Freight & Capacity
   - Geopolitical Risk & Trade Policy Regulations
   - Supply Chain Network Design
4. Minimize generic jargon; focus on actionable routing, capacity, or regulatory impacts.
5. Provide explicit citations and URLs for every data point.
6. Return your output as clean, semantic HTML (<p>, <ul>, <li>, <strong>, <h3>).

SOURCE DATA:
{compiled_context}
"""

    print("Generating briefing with Claude...")
    claude_response_raw = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=180
    )
    
    claude_response = claude_response_raw.json()

    # Check if Anthropic returned an error instead of a briefing
    if "error" in claude_response:
        print(f"ANTHROPIC API ERROR: {claude_response['error']}")
        return

    briefing_html = claude_response["content"][0]["text"]
    date_str = datetime.now().strftime("%B %d, %Y")
    subject = f"Global Logistics & Trade Briefing — {date_str}")

    full_email_html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: auto; padding: 20px;">
        <div style="border-bottom: 2px solid #0052cc; padding-bottom: 8px; margin-bottom: 24px;">
            <h1 style="font-size: 24px; margin: 0; color: #111;">{subject}</h1>
            <p style="color: #666; font-size: 14px; margin: 4px 0 0;">Weekly Macroeconomic Synthesis</p>
        </div>
        {briefing_html}
    </body>
    </html>
    """

    print("Sending email...")
    SES_CLIENT.send_email(
        Source="adam.karson@gmail.com",
        Destination={"ToAddresses": ["adam.karson@expeditors.com", "adam.karson@gmail.com"]},
        Message={
            "Subject": {"Data": subject},
            "Body": {"Html": {"Data": full_email_html}}
        }
    )
    print("Briefing delivered successfully.")

if __name__ == "__main__":
    main()
