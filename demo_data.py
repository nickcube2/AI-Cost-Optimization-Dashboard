#!/usr/bin/env python3
"""
Demo Data Generator
===================

Provides deterministic sample data for local demos without AWS access.
"""

from datetime import datetime, timedelta


def _daily_costs(start_date, days, base, drift=0.2, jitter=0.3):
    """
    Create a list of daily costs with slight trend and variability.
    """
    costs = []
    for i in range(days):
        day = start_date + timedelta(days=i)
        # Simple deterministic pattern (no randomness) for stable demos
        wave = ((i % 7) - 3) * 0.12
        trend = drift * (i / max(days - 1, 1))
        cost = max(0.5, base + base * (wave + trend) + (jitter * ((i % 3) - 1)))
        costs.append({"date": day.strftime("%Y-%m-%d"), "cost": round(cost, 2)})
    return costs


def get_demo_multi_account_data(days: int = 7):
    """
    Build demo multi-account data matching MultiAccountAnalyzer output shape.
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    prod_daily = _daily_costs(start_date, days, base=280.0, drift=0.25, jitter=1.5)
    staging_daily = _daily_costs(start_date, days, base=85.0, drift=0.05, jitter=0.6)
    dev_daily = _daily_costs(start_date, days, base=35.0, drift=-0.03, jitter=0.4)

    prod_services = {
        "Amazon EC2": 860.25,
        "Amazon RDS": 420.10,
        "Amazon S3": 180.60,
        "AWS Lambda": 95.40,
        "NAT Gateway": 72.25,
        "AWS KMS": 33.10,
    }

    staging_services = {
        "Amazon EC2": 210.40,
        "Amazon RDS": 98.15,
        "Amazon S3": 55.30,
        "AWS Lambda": 22.90,
        "NAT Gateway": 18.60,
    }

    dev_services = {
        "Amazon EC2": 75.50,
        "Amazon S3": 28.15,
        "AWS Lambda": 16.30,
        "Amazon CloudWatch": 9.80,
    }

    def total_cost(daily_costs):
        return round(sum(day["cost"] for day in daily_costs), 2)

    accounts = {
        "prod": {
            "total_cost": total_cost(prod_daily),
            "by_service": prod_services,
            "daily_costs": prod_daily,
            "top_service": "Amazon EC2",
            "service_count": len(prod_services),
        },
        "staging": {
            "total_cost": total_cost(staging_daily),
            "by_service": staging_services,
            "daily_costs": staging_daily,
            "top_service": "Amazon EC2",
            "service_count": len(staging_services),
        },
        "dev": {
            "total_cost": total_cost(dev_daily),
            "by_service": dev_services,
            "daily_costs": dev_daily,
            "top_service": "Amazon EC2",
            "service_count": len(dev_services),
        },
    }

    total_all = round(sum(a["total_cost"] for a in accounts.values()), 2)

    return {
        "accounts": accounts,
        "total_all_accounts": total_all,
        "period_days": days,
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "start_date": start_str,
        "end_date": end_str,
        "demo": True,
    }


def get_demo_recommendations():
    """
    Seed demo recommendations for the savings tracker.
    """
    return [
        {
            "title": "Downsize EC2 m5.4xlarge to m5.xlarge (prod)",
            "type": "EC2_rightsizing",
            "savings": 420.0,
            "description": "CPU < 15% over 30 days; safe resize during maintenance window",
            "risk": "low",
            "effort": "quick_win",
            "implemented": True,
            "actual_savings": 400.0,
        },
        {
            "title": "Add S3 lifecycle policy to enable Intelligent-Tiering (prod)",
            "type": "S3_lifecycle",
            "savings": 120.0,
            "description": "80% objects untouched for 45+ days",
            "risk": "low",
            "effort": "quick_win",
        },
        {
            "title": "Consolidate NAT gateways across AZs (staging/dev)",
            "type": "network_optimization",
            "savings": 95.0,
            "description": "Low traffic in non-prod; use single NAT gateway",
            "risk": "medium",
            "effort": "medium",
        },
    ]
