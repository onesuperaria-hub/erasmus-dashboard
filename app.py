#!/usr/bin/env python3
"""
Erasmus Home Page Dashboard - Flask web application.
"""

from flask import Flask, render_template
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add utils to path
sys.path.append(str(Path(__file__).parent / "utils"))
from cost_tracker import get_db_path, get_sessions_summary, format_currency, format_tokens, get_daily_costs_last_n_days

app = Flask(__name__)

def prepare_summary_data():
    """Prepare dashboard summary data."""
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
    
    # Format model data for template
    for model, data in summary["by_model"].items():
        data["input_tokens_formatted"] = format_tokens(data["input_tokens"])
        data["output_tokens_formatted"] = format_tokens(data["output_tokens"])
        data["calculated_cost_formatted"] = format_currency(data["calculated_cost"])
    
    # Convert None model keys to "Unknown" for JSON serialization
    by_model_fixed = {}
    for model, data in summary["by_model"].items():
        key = str(model) if model is not None else "Unknown"
        by_model_fixed[key] = data
    summary["by_model"] = by_model_fixed

    # Prepare chart data
    daily_labels = [day["date"] for day in daily_costs]
    daily_costs_values = [day["cost"] for day in daily_costs]
    
    # Top 10 models by cost for pie chart
    # Ensure model names are strings for sorting stability
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

@app.route("/")
def index():
    """Main dashboard page."""
    summary = prepare_summary_data()
    if "error" in summary:
        return render_template("error.html", error=summary["error"])
    return render_template("index.html", summary=summary, 
                          daily_labels=summary["daily_labels"],
                          daily_costs=summary["daily_costs"],
                          model_names=summary["model_names"],
                          model_costs=summary["model_costs"])

@app.route("/api/summary")
def api_summary():
    """JSON API for summary data."""
    summary = prepare_summary_data()
    return summary

@app.route("/system")
def system_status():
    """System monitoring page."""
    return "System status page - coming soon"

@app.route("/logs")
def logs():
    """Log viewer page."""
    return "Log viewer - coming soon"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)