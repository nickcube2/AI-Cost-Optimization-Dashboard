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
from datetime import datetime
from dotenv import load_dotenv

# Import our modules
from multi_account_analyzer import MultiAccountAnalyzer, print_multi_account_summary
from cost_forecaster import CostForecaster, print_forecast_summary, print_budget_alert
from savings_tracker import SavingsTracker, print_roi_dashboard
from auto_remediator import AutoRemediator, print_remediation_plan
from demo_data import get_demo_multi_account_data, get_demo_recommendations
from anomaly_detector import detect_anomalies, print_anomaly_summary

# Load configuration
load_dotenv()

def parse_args(argv):
    """
    Parse simple CLI flags without external dependencies.
    """
    return {
        "demo": "--demo" in argv,
        "ai_forecast": "--ai-forecast" in argv,
        "auto_remediate": "--auto-remediate" in argv,
        "generate_terraform": "--generate-terraform" in argv,
        "report": "--report" in argv or "--demo" in argv,
    }


def save_advanced_report(
    report_path,
    multi_account_data,
    roi,
    forecast,
    budget_check,
    cross_account_recs,
    pending_recs,
    anomaly_result,
    demo_mode=False,
):
    """
    Save a formatted report to a local file.
    """
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    lines = []
    lines.append("=" * 70)
    lines.append("AI COST OPTIMIZATION REPORT")
    lines.append("=" * 70)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Period: {multi_account_data['start_date']} to {multi_account_data['end_date']}")
    lines.append(f"Accounts: {len(multi_account_data['accounts'])}")
    lines.append(f"Total Spend: ${multi_account_data['total_all_accounts']:.2f}")
    if demo_mode:
        lines.append("Mode: DEMO (sample data)")
    lines.append("")

    lines.append("PER-ACCOUNT SUMMARY")
    lines.append("-" * 70)
    for account_name, data in multi_account_data["accounts"].items():
        if "error" in data and "total_cost" not in data:
            lines.append(f"{account_name}: ERROR - {data['error']}")
            continue
        lines.append(f"{account_name}: ${data['total_cost']:.2f}")
        if "by_service" in data:
            top_services = list(data["by_service"].items())[:3]
            for service, cost in top_services:
                lines.append(f"  - {service}: ${cost:.2f}")
    lines.append("")

    lines.append("COST FORECAST")
    lines.append("-" * 70)
    if forecast and "error" not in forecast:
        lines.append(f"Projected 30-Day Spend: ${forecast['projected_total']:.2f}")
        lines.append(f"Monthly Run Rate: ${forecast['monthly_run_rate']:.2f}")
        lines.append(f"Confidence: {forecast['confidence']}")
        lines.append(f"Trend: {forecast['trend']} ({forecast['growth_rate']:+.1f}%)")
    else:
        lines.append("Forecast unavailable (insufficient data)")
    lines.append("")

    lines.append("BUDGET STATUS")
    lines.append("-" * 70)
    if budget_check and "error" not in budget_check:
        if budget_check.get("alert"):
            lines.append("Status: ALERT")
            lines.append(f"Projected Spend: ${budget_check['projected_spend']:.2f}")
            lines.append(f"Overage: ${budget_check['overage']:.2f} ({budget_check['overage_percent']:.1f}%)")
            lines.append(f"Estimated Exceed Date: {budget_check['estimated_date']}")
        else:
            lines.append("Status: On track")
            lines.append(f"Projected Spend: ${budget_check['projected_spend']:.2f}")
            lines.append(f"Buffer: ${budget_check['buffer']:.2f} ({budget_check['buffer_percent']:.1f}%)")
    else:
        lines.append("Budget check unavailable")
    lines.append("")

    lines.append("ANOMALY DETECTION")
    lines.append("-" * 70)
    if anomaly_result and anomaly_result.get("summary", {}).get("status") == "insufficient_data":
        lines.append("Insufficient data to detect anomalies.")
    elif anomaly_result and anomaly_result.get("anomalies"):
        for item in anomaly_result["anomalies"]:
            lines.append(f"- {item['date']}: ${item['cost']:.2f} (z={item['z_score']}, {item['severity']})")
    else:
        lines.append("No anomalies detected.")
    lines.append("")

    if cross_account_recs:
        lines.append("CROSS-ACCOUNT INSIGHTS")
        lines.append("-" * 70)
        for rec in cross_account_recs:
            lines.append(f"- {rec.get('title')}")
            if rec.get("description"):
                lines.append(f"  {rec['description']}")
        lines.append("")

    lines.append("SAVINGS TRACKER (ROI)")
    lines.append("-" * 70)
    lines.append(f"Total Recommendations: {roi['total_recommendations']}")
    lines.append(f"Implemented: {roi['implemented']}")
    lines.append(f"Pending: {roi['pending']}")
    lines.append(f"Estimated Savings: ${roi['total_estimated_savings']:.2f}/month")
    lines.append(f"Actual Savings: ${roi['total_actual_savings']:.2f}/month")
    lines.append(f"Annual Projection: ${roi['annual_projected_savings']:.2f}/year")
    lines.append("")

    if pending_recs:
        lines.append("TOP PENDING RECOMMENDATIONS")
        lines.append("-" * 70)
        for rec in pending_recs[:5]:
            lines.append(f"- {rec['title']} (${rec['estimated_monthly_savings']:.2f}/month)")
            lines.append(f"  Risk: {rec['risk_level']} | Effort: {rec['effort']}")
        lines.append("")

    with open(report_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    """
    Advanced cost optimization with all features enabled.
    """
    
    print("\n" + "=" * 70)
    print("🚀 ADVANCED AI COST OPTIMIZATION DASHBOARD")
    print("=" * 70 + "\n")
    
    args = parse_args(sys.argv)

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
    
    if args["demo"]:
        multi_account_data = get_demo_multi_account_data(days=days_to_analyze)
        print_multi_account_summary(multi_account_data)
        analyzer = MultiAccountAnalyzer("demo:default")
        cross_account_recs = analyzer.generate_cross_account_recommendations(multi_account_data)
    else:
        analyzer = MultiAccountAnalyzer(aws_accounts)
        multi_account_data = analyzer.get_multi_account_costs(days=days_to_analyze)
        print_multi_account_summary(multi_account_data)
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
    
    forecast = None
    budget_check = None

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
        if args["ai_forecast"] and claude_api_key:
            print("\n" + "=" * 70)
            print("🤖 AI-POWERED DETAILED FORECAST")
            print("=" * 70 + "\n")
            
            ai_forecast = forecaster.forecast_with_ai(account_data, forecast_days=30)
            print(ai_forecast)
            print("\n" + "=" * 70 + "\n")

    # =================================================================
    # STEP 2B: Cost Anomaly Detection
    # =================================================================

    anomaly_result = {}
    if 'daily_costs' in account_data:
        anomaly_result = detect_anomalies(account_data['daily_costs'])
        print_anomaly_summary(anomaly_result)
    
    # =================================================================
    # STEP 3: Savings Tracker
    # =================================================================
    
    print("\n" + "=" * 70)
    print("STEP 3: SAVINGS TRACKER & ROI")
    print("=" * 70)
    
    demo_db_path = "data/demo_savings_tracker.db"
    if args["demo"] and os.path.exists(demo_db_path):
        os.remove(demo_db_path)

    tracker = SavingsTracker(db_path=demo_db_path if args["demo"] else "data/savings_tracker.db")
    
    # Add current cost snapshot
    for account_name, account_data in multi_account_data['accounts'].items():
        if 'error' not in account_data:
            tracker.add_cost_snapshot(
                total_cost=account_data['total_cost'],
                account_name=account_name,
                period_days=days_to_analyze,
                service_breakdown=account_data.get('by_service')
            )

    # Seed demo recommendations for ROI clarity
    if args["demo"]:
        for rec in get_demo_recommendations():
            tracker.add_recommendation(
                title=rec["title"],
                recommendation_type=rec["type"],
                estimated_savings=rec["savings"],
                description=rec["description"],
                risk_level=rec["risk"],
                effort=rec["effort"],
                account_name="demo",
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
    
    if args["auto_remediate"]:
        print("\n" + "=" * 70)
        print("STEP 4: AUTO-REMEDIATION")
        print("=" * 70)
        
        remediator = AutoRemediator(claude_api_key, dry_run=True)
        
        # Create remediation plan from pending recommendations
        plan = remediator.create_remediation_plan(pending)
        print_remediation_plan(plan)
        
        if plan and args["generate_terraform"]:
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
    
    if args["report"]:
        report_name = f"advanced_cost_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path = os.path.join("reports", report_name)
        save_advanced_report(
            report_path=report_path,
            multi_account_data=multi_account_data,
            roi=roi,
            forecast=forecast if 'forecast' in locals() else None,
            budget_check=budget_check if 'budget_check' in locals() else None,
            cross_account_recs=cross_account_recs,
            pending_recs=pending,
            anomaly_result=anomaly_result,
            demo_mode=args["demo"],
        )
        print(f"💾 Report saved to: {report_path}")

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
