#!/usr/bin/env python3
"""
Advanced AI Cost Optimization Dashboard
========================================

Integrated version with all advanced features:
- Multi-account support
- Cost forecasting
- Savings tracking
- Auto-remediation

Author: Nicholas Awuni
"""

import os
import sys
from dotenv import load_dotenv

# Import our modules
from multi_account_analyzer import MultiAccountAnalyzer, print_multi_account_summary
from cost_forecaster import CostForecaster, print_forecast_summary, print_budget_alert
from savings_tracker import SavingsTracker, print_roi_dashboard
from auto_remediator import AutoRemediator, print_remediation_plan

# Load configuration
load_dotenv()

def main():
    """
    Advanced cost optimization with all features enabled.
    """
    
    print("\n" + "=" * 70)
    print("🚀 ADVANCED AI COST OPTIMIZATION DASHBOARD")
    print("=" * 70 + "\n")
    
    # Configuration
    aws_accounts = os.getenv('AWS_ACCOUNTS', 'default:default')
    claude_api_key = os.getenv('CLAUDE_API_KEY')
    days_to_analyze = int(os.getenv('DAYS_TO_ANALYZE', '7'))
    monthly_budget = float(os.getenv('MONTHLY_BUDGET', '1000'))
    
    print(f"📅 Analysis Period: {days_to_analyze} days")
    print(f"💰 Monthly Budget: ${monthly_budget:.2f}")
    print(f"🏢 Accounts: {len(aws_accounts.split(','))}")
    print()
    
    # =================================================================
    # STEP 1: Multi-Account Cost Analysis
    # =================================================================
    
    print("=" * 70)
    print("STEP 1: MULTI-ACCOUNT COST ANALYSIS")
    print("=" * 70)
    
    analyzer = MultiAccountAnalyzer(aws_accounts)
    multi_account_data = analyzer.get_multi_account_costs(days=days_to_analyze)
    
    print_multi_account_summary(multi_account_data)
    
    # Generate cross-account insights
    cross_account_recs = analyzer.generate_cross_account_recommendations(multi_account_data)
    
    if cross_account_recs:
        print("\n🔍 Cross-Account Insights:")
        for rec in cross_account_recs:
            print(f"  • {rec['title']}")
            print(f"    {rec['description']}\n")
    
    # =================================================================
    # STEP 2: Cost Forecasting
    # =================================================================
    
    print("\n" + "=" * 70)
    print("STEP 2: COST FORECASTING")
    print("=" * 70)
    
    forecaster = CostForecaster(claude_api_key)
    
    # Use first account's data for forecasting (or combined if single account)
    first_account = list(multi_account_data['accounts'].keys())[0]
    account_data = multi_account_data['accounts'][first_account]
    
    if 'error' not in account_data:
        # Simple statistical forecast
        forecast = forecaster.simple_forecast(account_data, forecast_days=30)
        print_forecast_summary(forecast)
        
        # Budget alert
        budget_check = forecaster.budget_alert(account_data, monthly_budget)
        print_budget_alert(budget_check)
        
        # AI-powered forecast (if enabled)
        if '--ai-forecast' in sys.argv and claude_api_key:
            print("\n" + "=" * 70)
            print("🤖 AI-POWERED DETAILED FORECAST")
            print("=" * 70 + "\n")
            
            ai_forecast = forecaster.forecast_with_ai(account_data, forecast_days=30)
            print(ai_forecast)
            print("\n" + "=" * 70 + "\n")
    
    # =================================================================
    # STEP 3: Savings Tracker
    # =================================================================
    
    print("\n" + "=" * 70)
    print("STEP 3: SAVINGS TRACKER & ROI")
    print("=" * 70)
    
    tracker = SavingsTracker()
    
    # Add current cost snapshot
    for account_name, account_data in multi_account_data['accounts'].items():
        if 'error' not in account_data:
            tracker.add_cost_snapshot(
                total_cost=account_data['total_cost'],
                account_name=account_name,
                period_days=days_to_analyze,
                service_breakdown=account_data.get('by_service')
            )
    
    # Show ROI dashboard
    roi = tracker.get_roi_summary()
    print_roi_dashboard(roi)
    
    # Show pending recommendations
    pending = tracker.get_recommendations(status='pending')
    if pending:
        print("⏳ Pending Recommendations:")
        for rec in pending[:5]:  # Top 5
            print(f"  • {rec['title']}")
            print(f"    Est. Savings: ${rec['estimated_monthly_savings']:.2f}/month")
            print(f"    Risk: {rec['risk_level']} | Effort: {rec['effort']}\n")
    
    # =================================================================
    # STEP 4: Auto-Remediation (if enabled)
    # =================================================================
    
    if '--auto-remediate' in sys.argv:
        print("\n" + "=" * 70)
        print("STEP 4: AUTO-REMEDIATION")
        print("=" * 70)
        
        remediator = AutoRemediator(claude_api_key, dry_run=True)
        
        # Create remediation plan from pending recommendations
        plan = remediator.create_remediation_plan(pending)
        print_remediation_plan(plan)
        
        if plan and '--generate-terraform' in sys.argv:
            print("\n🔧 Generating Terraform code...\n")
            
            for item in plan[:3]:  # Limit to 3 for demo
                terraform_code = remediator.generate_terraform_for_optimization(
                    item['optimization_type'],
                    item['details']
                )
                
                filename = f"{item['optimization_type'].lower()}_{item.get('recommendation_id', 'demo')}.tf"
                filepath = remediator.save_terraform_file(terraform_code, filename)
                
                print(f"✅ Generated: {filepath}")
            
            print("\n⚠️  DRY RUN MODE: Review generated Terraform before applying!")
            print("To apply: cd terraform_generated && terraform plan\n")
    
    # =================================================================
    # SUMMARY
    # =================================================================
    
    print("\n" + "=" * 70)
    print("📊 EXECUTIVE SUMMARY")
    print("=" * 70 + "\n")
    
    print(f"Total Spend: ${multi_account_data['total_all_accounts']:.2f}")
    print(f"Accounts Analyzed: {len(multi_account_data['accounts'])}")
    
    if forecast and 'error' not in forecast:
        print(f"30-Day Forecast: ${forecast['projected_total']:.2f}")
        print(f"Monthly Run Rate: ${forecast['monthly_run_rate']:.2f}")
    
    print(f"\nRecommendations:")
    print(f"  Total: {roi['total_recommendations']}")
    print(f"  Implemented: {roi['implemented']}")
    print(f"  Pending: {roi['pending']}")
    
    if roi['total_actual_savings'] > 0:
        print(f"\nActual Savings Achieved: ${roi['total_actual_savings']:.2f}/month")
        print(f"Annual Projection: ${roi['annual_projected_savings']:.2f}/year")
    
    print("\n" + "=" * 70 + "\n")
    
    print("✅ Analysis complete!")
    print("\nNext steps:")
    print("  1. Review recommendations in savings tracker")
    print("  2. Run with --ai-forecast for detailed AI predictions")
    print("  3. Run with --auto-remediate to see auto-fix options")
    print("  4. Run with --generate-terraform to create IaC\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Analysis cancelled by user.\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)