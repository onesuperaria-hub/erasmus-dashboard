#!/usr/bin/env python3
"""
Erasmus Dashboard - Cloud version with authentication and remote data source.
"""

import os
import json
import logging
from flask import Flask, render_template, jsonify
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import requests

app = Flask(__name__)
auth = HTTPBasicAuth()

# Configuration
GIST_ID = os.environ.get('GIST_ID')  # GitHub Gist ID for data
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')  # Optional, for private gist
DASHBOARD_USER = os.environ.get('DASHBOARD_USER', 'admin')
DASHBOARD_PASSWORD = os.environ.get('DASHBOARD_PASSWORD', 'changeme')
LOCAL_MODE = os.environ.get('LOCAL_MODE', 'false').lower() == 'true'

# Users for HTTP Basic Auth
users = {
    DASHBOARD_USER: generate_password_hash(DASHBOARD_PASSWORD, method='pbkdf2:sha256')
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None

def fetch_from_gist():
    """Fetch summary data from GitHub Gist."""
    if not GIST_ID:
        return {"error": "GIST_ID not configured"}
    
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {}
    if GITHUB_TOKEN:
        headers['Authorization'] = f"token {GITHUB_TOKEN}"
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            gist_data = resp.json()
            # Look for a JSON file in the gist
            for filename, file_info in gist_data['files'].items():
                if filename.endswith('.json'):
                    content = file_info['content']
                    return json.loads(content)
        else:
            return {"error": f"GitHub API error: {resp.status_code}"}
    except Exception as e:
        return {"error": f"Failed to fetch gist: {str(e)}"}
    
    return {"error": "No JSON file found in gist"}

def prepare_summary_data():
    """Prepare dashboard summary data - from gist or local."""
    if LOCAL_MODE:
        # Local mode - import local modules
        try:
            from pathlib import Path
            import sys
            sys.path.append(str(Path(__file__).parent / "utils"))
            from cost_tracker import get_db_path, get_sessions_summary, format_currency, format_tokens, get_daily_costs_last_n_days
            
            db_path = get_db_path()
            if not db_path:
                return {"error": "Hermes database not found"}
            
            summary = get_sessions_summary(db_path, days_back=30)
            
            # Format totals
            total_tokens = (summary["total_input_tokens"] + 
                           summary["total_output_tokens"] + 
                           summary["total_reasoning_tokens"])
            
            summary["total_tokens_formatted"] = format_tokens(total_tokens)
            summary["total_calculated_cost_formatted"] = format_currency(summary["total_calculated_cost"])
            
            # Calculate average daily cost (last 7 days)
            daily_costs = get_daily_costs_last_n_days(db_path, days=7)
            avg_daily = sum(day["cost"] for day in daily_costs) / 7 if daily_costs else 0
            summary["avg_daily_cost_formatted"] = format_currency(avg_daily)
            
            # Format model data
            for model, data in summary["by_model"].items():
                data["input_tokens_formatted"] = format_tokens(data["input_tokens"])
                data["output_tokens_formatted"] = format_tokens(data["output_tokens"])
                data["calculated_cost_formatted"] = format_currency(data["calculated_cost"])
            
            # Convert None model keys
            by_model_fixed = {}
            for model, data in summary["by_model"].items():
                key = str(model) if model is not None else "Unknown"
                by_model_fixed[key] = data
            summary["by_model"] = by_model_fixed
            
            # Prepare chart data
            daily_labels = [day["date"] for day in daily_costs]
            daily_costs_values = [day["cost"] for day in daily_costs]
            
            # Top 10 models
            model_items = []
            for model, data in summary["by_model"].items():
                safe_model = str(model) if model is not None else "Unknown"
                model_items.append((safe_model, data))
            
            model_items = sorted(model_items, 
                                key=lambda x: (x[1]["calculated_cost"], x[0]), reverse=True)[:10]
            model_names = [(model[:30] + ("..." if len(model) > 30 else "")) for model, _ in model_items]
            model_costs = [data["calculated_cost"] for _, data in model_items]
            
            summary["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            summary["daily_labels"] = daily_labels
            summary["daily_costs"] = daily_costs_values
            summary["model_names"] = model_names
            summary["model_costs"] = model_costs
            
            return summary
            
        except ImportError as e:
            return {"error": f"Local mode import failed: {str(e)}"}
    else:
        # Cloud mode - fetch from gist
        data = fetch_from_gist()
        if "error" in data:
            return data
        
        # Ensure all required fields exist
        required = ["total_sessions", "total_calculated_cost", "total_tokens_formatted",
                   "total_calculated_cost_formatted", "avg_daily_cost_formatted",
                   "by_model", "timestamp", "daily_labels", "daily_costs",
                   "model_names", "model_costs"]
        
        for field in required:
            if field not in data:
                data[field] = None if field != "by_model" else {}
        
        return data

@app.route("/")
@auth.login_required
def index():
    """Main dashboard page."""
    summary = prepare_summary_data()
    if "error" in summary:
        return render_template("error.html", error=summary["error"])
    
    return render_template("index.html", summary=summary,
                          daily_labels=summary.get("daily_labels", []),
                          daily_costs=summary.get("daily_costs", []),
                          model_names=summary.get("model_names", []),
                          model_costs=summary.get("model_costs", []))

@app.route("/api/summary")
@auth.login_required
def api_summary():
    """JSON API for summary data."""
    summary = prepare_summary_data()
    return jsonify(summary)

@app.route("/system")
@auth.login_required
def system_status():
    """System monitoring page."""
    return "System status page - coming soon"

@app.route("/logs")
@auth.login_required
def logs():
    """Log viewer page."""
    return "Log viewer - coming soon"

@app.route("/health")
@auth.login_required(optional=True)
def health():
    """Health check endpoint (no auth required)."""
    return jsonify({"status": "ok", "mode": "local" if LOCAL_MODE else "cloud"})

if __name__ == "__main__":
    # Log configuration
    logging.basicConfig(level=logging.INFO)
    app.run(debug=LOCAL_MODE, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))