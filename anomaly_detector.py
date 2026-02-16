#!/usr/bin/env python3
"""
Cost Anomaly Detector
=====================

Detects unusual spend spikes using simple statistical methods.
"""

from typing import Dict, List


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _stddev(values: List[float], mean: float) -> float:
    if not values:
        return 0.0
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance ** 0.5


def _percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * p
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


def detect_anomalies(daily_costs: List[Dict], z_threshold: float = 2.5) -> Dict:
    """
    Detect anomalies from daily cost series.

    Args:
        daily_costs: List of {'date': 'YYYY-MM-DD', 'cost': float}
        z_threshold: Z-score threshold for anomaly

    Returns:
        Dict with anomalies list and summary stats
    """
    if not daily_costs or len(daily_costs) < 7:
        return {
            "anomalies": [],
            "summary": {
                "status": "insufficient_data",
                "message": "Need at least 7 days to detect anomalies"
            }
        }

    costs = [day["cost"] for day in daily_costs]
    avg = _mean(costs)
    std = _stddev(costs, avg)

    q1 = _percentile(costs, 0.25)
    q3 = _percentile(costs, 0.75)
    iqr = q3 - q1
    upper_iqr = q3 + 1.5 * iqr

    anomalies = []
    for day in daily_costs:
        cost = day["cost"]
        z_score = (cost - avg) / std if std > 0 else 0.0

        is_z = z_score >= z_threshold
        is_iqr = cost > upper_iqr

        if is_z or is_iqr:
            severity = "medium"
            if z_score >= 3.5 or cost > (q3 + 3 * iqr):
                severity = "high"

            anomalies.append({
                "date": day["date"],
                "cost": round(cost, 2),
                "z_score": round(z_score, 2),
                "severity": severity,
                "reason": "z-score" if is_z else "iqr"
            })

    status = "ok" if anomalies else "none"

    return {
        "anomalies": anomalies,
        "summary": {
            "status": status,
            "average_daily": round(avg, 2),
            "stddev": round(std, 2),
            "q1": round(q1, 2),
            "q3": round(q3, 2)
        }
    }


def print_anomaly_summary(result: Dict):
    """
    Print formatted anomaly results.
    """
    anomalies = result.get("anomalies", [])
    summary = result.get("summary", {})

    print("\n" + "=" * 70)
    print("🚨 COST ANOMALY DETECTION")
    print("=" * 70 + "\n")

    if summary.get("status") == "insufficient_data":
        print("⚠️  Insufficient data to detect anomalies.\n")
        return

    if not anomalies:
        print("✅ No anomalies detected.")
        print(f"Average Daily Cost: ${summary.get('average_daily', 0):.2f}")
        print(f"Std Dev: ${summary.get('stddev', 0):.2f}")
        print("\n" + "=" * 70 + "\n")
        return

    print(f"Found {len(anomalies)} anomaly(ies):\n")
    for item in anomalies:
        print(f"- {item['date']}: ${item['cost']:.2f} (z={item['z_score']}, {item['severity']})")

    print("\n" + "=" * 70 + "\n")
