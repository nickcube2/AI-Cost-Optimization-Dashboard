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
from functools import wraps
from flask import Flask, jsonify, render_template, request, Response, abort

from dashboard_data import build_dashboard_payload

app = Flask(__name__, static_folder="static", template_folder="templates")

API_TOKEN = os.getenv("DASHBOARD_API_TOKEN", "").strip()
DEFAULT_HOST = os.getenv("DASHBOARD_HOST", "127.0.0.1")
CACHE_TTL = int(os.getenv("DASHBOARD_CACHE_TTL", "60"))

_cache = {"ts": 0, "key": None, "payload": None}


def require_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not API_TOKEN:
            return func(*args, **kwargs)
        token = request.headers.get("X-API-Token") or request.args.get("token")
        if token != API_TOKEN:
            abort(401)
        return func(*args, **kwargs)

    return wrapper


def _cache_key(mode, days, budget, accounts):
    return f"{mode}:{days}:{budget}:{accounts}"


def get_cached_payload(mode, days, budget, accounts):
    now = time.time()
    key = _cache_key(mode, days, budget, accounts)
    if _cache["payload"] and _cache["key"] == key and (now - _cache["ts"]) < CACHE_TTL:
        return _cache["payload"]

    payload = build_dashboard_payload(
        mode=mode,
        days=days,
        monthly_budget=budget,
        accounts_config=accounts,
    )
    _cache.update({"ts": now, "key": key, "payload": payload})
    return payload


@app.route("/")
def index():
    return render_template("index.html", token_required=bool(API_TOKEN))


@app.route("/api/summary")
@require_token
def api_summary():
    mode = request.args.get("mode", os.getenv("DASHBOARD_MODE", "demo"))
    days = int(request.args.get("days", os.getenv("DAYS_TO_ANALYZE", "7")))
    budget = float(request.args.get("budget", os.getenv("MONTHLY_BUDGET", "1000")))
    accounts = request.args.get("accounts", os.getenv("AWS_ACCOUNTS", "default:default"))

    payload = get_cached_payload(mode, days, budget, accounts)
    return jsonify(payload)


@app.route("/api/stream")
@require_token
def api_stream():
    mode = request.args.get("mode", os.getenv("DASHBOARD_MODE", "demo"))
    days = int(request.args.get("days", os.getenv("DAYS_TO_ANALYZE", "7")))
    budget = float(request.args.get("budget", os.getenv("MONTHLY_BUDGET", "1000")))
    accounts = request.args.get("accounts", os.getenv("AWS_ACCOUNTS", "default:default"))
    interval = int(request.args.get("interval", os.getenv("SSE_INTERVAL", "30")))

    def event_stream():
        while True:
            payload = get_cached_payload(mode, days, budget, accounts)
            data = json.dumps(payload)
            yield f"event: summary\ndata: {data}\n\n"
            time.sleep(max(5, interval))

    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host=DEFAULT_HOST, port=port, debug=debug)
