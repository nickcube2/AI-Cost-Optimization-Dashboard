#!/usr/bin/env python3
"""
Flask Web Dashboard
===================

Run: python app.py
Then open http://localhost:5000
"""

import os
import json
import time
from flask import Flask, jsonify, render_template, request, Response

from dashboard_data import build_dashboard_payload

app = Flask(__name__, static_folder="static", template_folder="templates")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/summary")
def api_summary():
    mode = request.args.get("mode", os.getenv("DASHBOARD_MODE", "demo"))
    days = int(request.args.get("days", os.getenv("DAYS_TO_ANALYZE", "7")))
    budget = float(request.args.get("budget", os.getenv("MONTHLY_BUDGET", "1000")))
    accounts = request.args.get("accounts", os.getenv("AWS_ACCOUNTS", "default:default"))

    payload = build_dashboard_payload(
        mode=mode,
        days=days,
        monthly_budget=budget,
        accounts_config=accounts,
    )
    return jsonify(payload)


@app.route("/api/stream")
def api_stream():
    mode = request.args.get("mode", os.getenv("DASHBOARD_MODE", "demo"))
    days = int(request.args.get("days", os.getenv("DAYS_TO_ANALYZE", "7")))
    budget = float(request.args.get("budget", os.getenv("MONTHLY_BUDGET", "1000")))
    accounts = request.args.get("accounts", os.getenv("AWS_ACCOUNTS", "default:default"))
    interval = int(request.args.get("interval", os.getenv("SSE_INTERVAL", "30")))

    def event_stream():
        while True:
            payload = build_dashboard_payload(
                mode=mode,
                days=days,
                monthly_budget=budget,
                accounts_config=accounts,
            )
            data = json.dumps(payload)
            yield f"event: summary\ndata: {data}\n\n"
            time.sleep(max(5, interval))

    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
