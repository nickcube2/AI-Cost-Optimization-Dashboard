#!/usr/bin/env python3
"""
AI Cost Optimization Dashboard
================================

This script analyzes your AWS spending and uses Claude AI to generate
actionable cost-saving recommendations.

Author: Nicholas Awuni
Purpose: AI-powered DevOps automation for cost optimization
Project: Part of AI-Powered DevOps Portfolio Series
"""

# ============================================================================
# IMPORTS - These are the libraries we need
# ============================================================================

# Standard library imports (come with Python)
import os
from datetime import datetime, timedelta
import json

# Third-party imports (installed via pip)
import boto3  # AWS SDK for Python
from anthropic import Anthropic  # Claude AI API
from dotenv import load_dotenv  # Load environment variables from .env file
import requests  # For sending HTTP requests to Slack

# ============================================================================
# CONFIGURATION - Load settings from .env file
# ============================================================================

# Load environment variables from .env file
# This keeps sensitive info (API keys) out of the code
load_dotenv()

# Get configuration from environment variables
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
DAYS_TO_ANALYZE = int(os.getenv('DAYS_TO_ANALYZE', '7'))

# ============================================================================
# FUNCTION: Print Cost Chart
# ============================================================================

def print_cost_chart(costs_by_service, max_width=50):
    """
    Print a simple ASCII bar chart of costs by service.
    
    Args:
        costs_by_service (dict): Service names and costs
        max_width (int): Maximum width of bars in characters
    """
    if not costs_by_service:
        return
    
    max_cost = max(costs_by_service.values())
    
    print("\n💰 Cost Distribution:")
    print("-" * 70)
    
    for service, cost in list(costs_by_service.items())[:10]:  # Top 10
        # Calculate bar length proportional to cost
        bar_length = int((cost / max_cost) * max_width)
        bar = "█" * bar_length
        
        # Format service name (shorten if needed)
        service_short = service.replace("Amazon ", "").replace("AWS ", "")
        if len(service_short) > 20:
            service_short = service_short[:17] + "..."
        
        # Print the bar
        print(f"{service_short:20} {bar} ${cost:>10.2f}")
    
    print("-" * 70 + "\n")

# ============================================================================
# FUNCTION: Get AWS Cost Data
# ============================================================================

def get_aws_costs(days=7, compare_previous=True):
    """
    Fetch AWS cost data from Cost Explorer API.
    
    Args:
        days (int): Number of days to analyze (default: 7)
        compare_previous (bool): Compare with previous period for trend analysis
    
    Returns:
        dict: Cost data organized by service and time period
    
    Example output:
        {
            'total_cost': 1234.56,
            'by_service': {'EC2': 500.00, 'S3': 100.00},
            'daily_costs': [...],
            'previous_period_cost': 1100.00,
            'change_percent': 12.2,
            'change_direction': 'up'
        }
    """
    
    print(f"📊 Fetching AWS cost data for last {days} days...")
    
    # Step 1: Create AWS Cost Explorer client
    # This is how we talk to AWS Cost Explorer API
    client = boto3.client('ce', region_name=AWS_REGION)
    
    # Step 2: Calculate date range
    # Cost Explorer needs dates in YYYY-MM-DD format
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Convert dates to strings in the format AWS expects
    end_str = end_date.strftime('%Y-%m-%d')
    start_str = start_date.strftime('%Y-%m-%d')
    
    print(f"   📅 Date range: {start_str} to {end_str}")
    
    try:
        # Step 3: Make API call to get cost data
        # This asks AWS: "Show me costs grouped by service"
        response = client.get_cost_and_usage(
            TimePeriod={
                'Start': start_str,
                'End': end_str
            },
            Granularity='DAILY',  # Get daily breakdown
            Metrics=['UnblendedCost'],  # The actual amount charged
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'  # Group costs by AWS service (EC2, S3, etc.)
                }
            ]
        )
        
        # Step 4: Process the response
        # AWS returns complex nested data, so we'll simplify it
        
        total_cost = 0.0
        costs_by_service = {}
        daily_costs = []
        
        # Loop through each day's results
        for day_result in response['ResultsByTime']:
            day_date = day_result['TimePeriod']['Start']
            day_total = 0.0
            
            # Loop through each service for this day
            for group in day_result['Groups']:
                service_name = group['Keys'][0]  # e.g., "Amazon EC2"
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                
                # Add to running totals
                day_total += cost
                
                # Track cost by service (sum across all days)
                if service_name in costs_by_service:
                    costs_by_service[service_name] += cost
                else:
                    costs_by_service[service_name] = cost
            
            daily_costs.append({
                'date': day_date,
                'cost': round(day_total, 2)
            })
            
            total_cost += day_total
        
        # Step 5: Create clean summary
        result = {
            'total_cost': round(total_cost, 2),
            'period_days': days,
            'start_date': start_str,
            'end_date': end_str,
            'by_service': {
                # Sort services by cost (highest first)
                service: round(cost, 2)
                for service, cost in sorted(
                    costs_by_service.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            },
            'daily_costs': daily_costs
        }
        
        # Step 6: Compare with previous period (trend analysis)
        if compare_previous and total_cost > 0:
            try:
                previous_start = start_date - timedelta(days=days)
                previous_end = start_date
                
                prev_response = client.get_cost_and_usage(
                    TimePeriod={
                        'Start': previous_start.strftime('%Y-%m-%d'),
                        'End': previous_end.strftime('%Y-%m-%d')
                    },
                    Granularity='DAILY',
                    Metrics=['UnblendedCost']
                )
                
                # Calculate previous period total
                previous_total = 0.0
                for day_result in prev_response['ResultsByTime']:
                    for group in day_result.get('Groups', []):
                        previous_total += float(group['Metrics']['UnblendedCost']['Amount'])
                
                # Calculate change percentage
                if previous_total > 0:
                    change_pct = ((total_cost - previous_total) / previous_total) * 100
                    result['previous_period_cost'] = round(previous_total, 2)
                    result['change_percent'] = round(change_pct, 2)
                    result['change_direction'] = "up" if change_pct > 0 else "down"
                    
                    print(f"   📈 Trend: {result['change_direction']} {abs(change_pct):.1f}% vs previous {days} days")
            
            except Exception as e:
                print(f"   ⚠️  Could not fetch previous period data: {str(e)[:50]}")
        
        print(f"   ✅ Retrieved cost data: ${result['total_cost']:.2f} total")
        print(f"   📦 Services found: {len(result['by_service'])}")
        
        return result
        
    except Exception as e:
        # If something goes wrong, print error and return empty data
        print(f"   ❌ Error fetching AWS costs: {str(e)}")
        return {
            'total_cost': 0.0,
            'by_service': {},
            'daily_costs': [],
            'error': str(e)
        }


# ============================================================================
# FUNCTION: Analyze Costs with Claude AI
# ============================================================================

def analyze_costs_with_ai(cost_data):
    """
    Send cost data to Claude AI for analysis and recommendations.
    
    Args:
        cost_data (dict): The cost data from get_aws_costs()
    
    Returns:
        str: AI-generated analysis and recommendations
    """
    
    print("🤖 Analyzing costs with Claude AI...")
    
    # Step 1: Check if we have an API key
    if not CLAUDE_API_KEY:
        return "⚠️ Claude API key not found. Please add it to your .env file."
    
    # Step 2: Create Anthropic client
    client = Anthropic(api_key=CLAUDE_API_KEY)
    
    # Step 3: Format cost data into a readable text for Claude
    cost_summary = f"""
AWS Cost Analysis Data ({cost_data.get('period_days', 7)} days)

Total Spend: ${cost_data.get('total_cost', 0):.2f}
Period: {cost_data.get('start_date')} to {cost_data.get('end_date')}

Costs by Service:
"""
    
    # Add each service's cost
    for service, cost in cost_data.get('by_service', {}).items():
        percentage = (cost / cost_data['total_cost'] * 100) if cost_data['total_cost'] > 0 else 0
        cost_summary += f"- {service}: ${cost:.2f} ({percentage:.1f}%)\n"
    
    # Step 4: Create the prompt for Claude
    # This tells Claude what we want it to do
    prompt = f"""You are a FinOps expert analyzing AWS spending for a production environment.

ANALYSIS REQUIREMENTS:
Provide insights in this exact format:

## 📊 SPENDING OVERVIEW
- Summary of total spend and trend
- Top 3 cost drivers (services consuming most)
- Any unusual spending patterns or anomalies

## 💰 OPTIMIZATION OPPORTUNITIES
For each recommendation, provide:
1. **What**: Specific resource/service to optimize
2. **Why**: Current inefficiency (e.g., "EC2 i3.2xlarge running 24/7 with 8% CPU")
3. **Action**: Exact AWS action to take (e.g., "Resize to t3.large via EC2 console")
4. **Savings**: Estimated monthly $ saved
5. **Risk**: Low/Medium/High (based on business impact)
6. **Effort**: Quick Win (< 1 hour) / Medium (1-4 hours) / Complex (> 4 hours)

FOCUS AREAS (prioritize by $ impact):
- Compute rightsizing (EC2, Lambda)
- Storage optimization (S3 classes, EBS volumes)
- Database efficiency (RDS instance sizing, unused snapshots)
- Network costs (data transfer, NAT gateways)
- Unused/idle resources

CONSTRAINTS:
- Only recommend changes with measurable $ impact
- Prioritize "Quick Wins" that save > $50/month
- Assume this is a production environment (avoid risky changes)

DATA TO ANALYZE:
{cost_summary}

Provide 3-5 recommendations ranked by ROI (savings / effort)."""

    try:
        # Step 5: Call Claude API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",  # Using Claude Sonnet 4
            max_tokens=1000,  # Limit response length
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Step 6: Extract the response text
        # Claude's response is in message.content[0].text
        analysis = message.content[0].text
        
        print("   ✅ AI analysis complete")
        
        return analysis
        
    except Exception as e:
        print(f"   ❌ Error calling Claude API: {str(e)}")
        return f"Error generating AI analysis: {str(e)}"


# ============================================================================
# FUNCTION: Send to Slack
# ============================================================================

def send_to_slack(cost_data, ai_analysis):
    """
    Send the cost analysis report to Slack via webhook.
    
    Args:
        cost_data (dict): Cost data summary
        ai_analysis (str): Claude's analysis text
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    
    # Skip if no webhook URL configured
    if not SLACK_WEBHOOK_URL:
        print("ℹ️  Slack webhook not configured, skipping notification")
        return False
    
    print("📬 Sending report to Slack...")
    
    # Create formatted message for Slack
    message = {
        "text": "🤖 Weekly AWS Cost Report",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🤖 AI-Powered AWS Cost Analysis"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Total Spend:* ${cost_data['total_cost']:.2f}\n*Period:* {cost_data['start_date']} to {cost_data['end_date']}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ai_analysis
                }
            }
        ]
    }
    
    try:
        # Send POST request to Slack webhook
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=message,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print("   ✅ Sent to Slack successfully")
            return True
        else:
            print(f"   ❌ Slack webhook failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error sending to Slack: {str(e)}")
        return False


# ============================================================================
# FUNCTION: Save Report to File
# ============================================================================

def save_report(cost_data, ai_analysis):
    """
    Save the analysis report to a local file.
    
    Args:
        cost_data (dict): Cost data summary
        ai_analysis (str): Claude's analysis text
    """
    
    # Create reports directory if it doesn't exist
    os.makedirs('reports', exist_ok=True)
    
    # Generate filename with current date
    filename = f"reports/cost_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    # Write report to file
    with open(filename, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("AWS COST OPTIMIZATION REPORT\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Period: {cost_data['start_date']} to {cost_data['end_date']}\n")
        f.write(f"Total Cost: ${cost_data['total_cost']:.2f}\n\n")
        f.write("-" * 70 + "\n")
        f.write("COST BREAKDOWN BY SERVICE\n")
        f.write("-" * 70 + "\n\n")
        
        for service, cost in cost_data['by_service'].items():
            f.write(f"{service}: ${cost:.2f}\n")
        
        f.write("\n" + "-" * 70 + "\n")
        f.write("AI ANALYSIS & RECOMMENDATIONS\n")
        f.write("-" * 70 + "\n\n")
        f.write(ai_analysis)
        f.write("\n\n" + "=" * 70 + "\n")
    
    print(f"💾 Report saved to: {filename}")


# ============================================================================
# MAIN FUNCTION - This runs when you execute the script
# ============================================================================

def main():
    """
    Main function that orchestrates the entire cost analysis process.
    """
    
    print("\n" + "=" * 70)
    print("🚀 AI COST OPTIMIZATION DASHBOARD")
    print("=" * 70 + "\n")
    
    # Step 1: Get AWS cost data
    cost_data = get_aws_costs(days=DAYS_TO_ANALYZE)
    
    # Check if we got data successfully
    if cost_data.get('error'):
        print("\n❌ Failed to retrieve AWS cost data. Please check:")
        print("   - AWS credentials are configured correctly")
        print("   - Cost Explorer is enabled in your AWS account")
        print("   - IAM user has ce:GetCostAndUsage permission")
        return
    
    if cost_data['total_cost'] == 0:
        print("\n⚠️  No cost data found for this period.")
        return
    
    # Step 2: Analyze costs with AI
    ai_analysis = analyze_costs_with_ai(cost_data)
    
    # Step 3: Display results in terminal
    print("\n" + "=" * 70)
    print("📊 COST SUMMARY")
    print("=" * 70 + "\n")
    print(f"Total Spend: ${cost_data['total_cost']:.2f}")
    print(f"Period: {cost_data['start_date']} to {cost_data['end_date']}")
    
    # Display trend if available
    if 'change_percent' in cost_data:
        direction_symbol = "↑" if cost_data['change_direction'] == "up" else "↓"
        trend_color = "📈" if cost_data['change_direction'] == "up" else "📉"
        print(f"\nTrend vs Previous Period: {trend_color} {direction_symbol} {abs(cost_data['change_percent']):.1f}%")
        print(f"Previous {cost_data['period_days']} days: ${cost_data['previous_period_cost']:.2f}")
    
    print(f"\nTop Services:")
    
    for i, (service, cost) in enumerate(list(cost_data['by_service'].items())[:5], 1):
        percentage = (cost / cost_data['total_cost'] * 100)
        print(f"{i}. {service}: ${cost:.2f} ({percentage:.1f}%)")
    
    # Display visual cost chart
    print_cost_chart(cost_data['by_service'])
    
    print("=" * 70)
    print("🤖 AI RECOMMENDATIONS")
    print("=" * 70 + "\n")
    print(ai_analysis)
    print("\n" + "=" * 70 + "\n")
    
    # Step 4: Save report to file
    save_report(cost_data, ai_analysis)
    
    # Step 5: Send to Slack (if configured)
    send_to_slack(cost_data, ai_analysis)
    
    print("\n✅ Analysis complete!\n")


# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # This runs when you execute: python cost_optimizer.py
    main()
