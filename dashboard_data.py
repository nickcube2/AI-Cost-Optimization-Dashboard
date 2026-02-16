#!/usr/bin/env python3
"""
Dashboard Data Builder
======================

Creates a JSON payload for the web UI, using demo or live AWS data.
"""

import os
from typing import Dict

from demo_data import get_demo_multi_account_data, get_demo_recommendations
from multi_account_analyzer import MultiAccountAnalyzer
from cost_forecaster import CostForecaster
from savings_tracker import SavingsTracker
from anomaly_detector import detect_anomalies
from auto_remediator import AutoRemediator


def _aggregate_services(multi_account_data: Dict) -> Dict:
    combined = {}
    for account_data in multi_account_data.get("accounts", {}).values():
        for service, cost in account_data.get("by_service", {}).items():
            combined[service] = round(combined.get(service, 0) + cost, 2)
    combined_sorted = dict(sorted(combined.items(), key=lambda x: x[1], reverse=True))
    return combined_sorted


def build_dashboard_payload(
    mode: str = "demo",
    days: int = 7,
    monthly_budget: float = 1000.0,
    accounts_config: str = "default:default",
) -> Dict:
    mode = (mode or "demo").lower()

    if mode == "demo":
        multi_account_data = get_demo_multi_account_data(days=days)
    else:
        analyzer = MultiAccountAnalyzer(accounts_config)
        multi_account_data = analyzer.get_multi_account_costs(days=days)

    # Use the first account for trend/anomaly/forecast visuals
    accounts_dict = multi_account_data.get("accounts", {})
    if accounts_dict:
        first_account = list(accounts_dict.keys())[0]
        account_data = accounts_dict[first_account]
    else:
        account_data = {
            "daily_costs": [],
            "by_service": {},
            "total_cost": 0.0,
        }

    # Forecast + budget
    forecaster = CostForecaster(provider=os.getenv("LLM_PROVIDER", "openai"))
    if mode == "demo" and monthly_budget < multi_account_data.get("total_all_accounts", 0.0):
        monthly_budget = round(multi_account_data.get("total_all_accounts", 0.0) * 1.1, 2)
    forecast = forecaster.simple_forecast(account_data, forecast_days=30)
    budget = forecaster.budget_alert(account_data, monthly_budget)

    # Anomaly detection
    anomalies = detect_anomalies(account_data.get("daily_costs", []))

    # Savings tracker
    if mode == "demo":
        db_path = "data/demo_savings_tracker.db"
        if os.path.exists(db_path):
            os.remove(db_path)
        tracker = SavingsTracker(db_path=db_path)
        for rec in get_demo_recommendations():
            rec_id = tracker.add_recommendation(
                title=rec["title"],
                recommendation_type=rec["type"],
                estimated_savings=rec["savings"],
                description=rec["description"],
                risk_level=rec["risk"],
                effort=rec["effort"],
                account_name="demo",
            )
            if rec.get("implemented"):
                tracker.mark_implemented(
                    rec_id,
                    actual_savings=rec.get("actual_savings"),
                    notes="Implemented in demo environment",
                )
    else:
        tracker = SavingsTracker(db_path="data/savings_tracker.db")

    roi = tracker.get_roi_summary()
    pending = tracker.get_recommendations(status="pending")[:5]
    remediator = AutoRemediator(provider=os.getenv("LLM_PROVIDER", "openai"), dry_run=True)
    remediation_plan = remediator.create_remediation_plan(pending)

    return {
        "meta": {
            "mode": mode,
            "days": days,
            "start_date": multi_account_data.get("start_date"),
            "end_date": multi_account_data.get("end_date"),
        },
        "totals": {
            "total_spend": multi_account_data.get("total_all_accounts", 0.0),
            "accounts": len(multi_account_data.get("accounts", {})),
        },
        "accounts": multi_account_data.get("accounts", {}),
        "services": _aggregate_services(multi_account_data),
        "daily_costs": account_data.get("daily_costs", []),
        "forecast": forecast,
        "budget": budget,
        "anomalies": anomalies,
        "roi": roi,
        "pending_recommendations": pending,
        "remediation_plan": remediation_plan,
    }
