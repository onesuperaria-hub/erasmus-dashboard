#!/usr/bin/env python3
"""
Erasmus Dashboard - Vercel compatible version
"""

import os
import json
import logging
from flask import Flask, render_template, jsonify, request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import requests

app = Flask(__name__)
auth = HTTPBasicAuth()

# Configuration
GIST_ID = os.environ.get('GIST_ID', '')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
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
            for filename, file_info in gist_data['files'].items():
                if filename.endswith('.json'):
                    content = file_info['content']
                    return json.loads(content)
        else:
            return {"error": f"GitHub API error: {resp.status_code}"}
    except Exception as e:
        return {"error": f"Failed to fetch gist: {str(e)}"}
    
    return {"error": "No JSON file found in gist"}

@app.route("/")
@auth.login_required
def index():
    """Main dashboard page."""
    # Return simple HTML dashboard
    html = """
<!DOCTYPE html>
<html>
<head>
    <title>Erasmus Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               background: #0f0f0f; color: #fff; min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        h1 { font-size: 1.5rem; margin-bottom: 20px; color: #00d4ff; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                 gap: 15px; margin-bottom: 30px; }
        .stat-card { background: #1a1a2e; border-radius: 12px; padding: 20px; 
                     border: 1px solid #2a2a4e; }
        .stat-card h3 { color: #888; font-size: 0.8rem; text-transform: uppercase; 
                        margin-bottom: 8px; }
        .stat-card .value { font-size: 1.8rem; font-weight: bold; color: #00d4ff; }
        .stat-card .value.warning { color: #ff6b6b; }
        .charts { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
        .chart-container { background: #1a1a2e; border-radius: 12px; padding: 20px; 
                          border: 1px solid #2a2a4e; height: 280px; }
        .chart-container h3 { margin-bottom: 15px; color: #888; font-size: 0.9rem; }
        table { width: 100%; border-collapse: collapse; background: #1a1a2e; 
                border-radius: 12px; overflow: hidden; }
        th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #2a2a4e; }
        th { background: #16162a; color: #888; font-weight: 600; font-size: 0.8rem; 
             text-transform: uppercase; }
        tr:hover { background: #1f1f3a; }
        .timestamp { text-align: right; color: #666; font-size: 0.8rem; margin-top: 20px; }
        .error { background: #3a1a1a; border: 1px solid #ff6b6b; border-radius: 12px; 
                 padding: 40px; text-align: center; }
        .error h2 { color: #ff6b6b; margin-bottom: 10px; }
        @media (max-width: 768px) { .charts { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>Erasmus Dashboard</h1>
        <div id="content">Loading...</div>
        <div class="timestamp" id="timestamp"></div>
    </div>
    <script>
        async function loadDashboard() {
            try {
                const resp = await fetch('/api/summary');
                const data = await resp.json();
                
                if (data.error) {
                    document.getElementById('content').innerHTML = 
                        '<div class="error"><h2>Error</h2><p>' + data.error + '</p></div>';
                    return;
                }
                
                const totalCost = data.total_calculated_cost || 0;
                const dailyCost = data.avg_daily_cost || 0;
                
                document.getElementById('content').innerHTML = `
                    <div class="stats">
                        <div class="stat-card">
                            <h3>Total Sessions</h3>
                            <div class="value">${data.total_sessions || 0}</div>
                        </div>
                        <div class="stat-card">
                            <h3>Total Cost</h3>
                            <div class="value ${totalCost > 50 ? 'warning' : ''}">${data.total_calculated_cost_formatted || '$0.00'}</div>
                        </div>
                        <div class="stat-card">
                            <h3>Total Tokens</h3>
                            <div class="value">${data.total_tokens_formatted || '0'}</div>
                        </div>
                        <div class="stat-card">
                            <h3>Avg Daily Cost</h3>
                            <div class="value">${data.avg_daily_cost_formatted || '$0.00'}</div>
                        </div>
                    </div>
                    
                    <div class="charts">
                        <div class="chart-container">
                            <h3>Daily Costs (Last 7 Days)</h3>
                            <canvas id="dailyChart"></canvas>
                        </div>
                        <div class="chart-container">
                            <h3>Top Models by Cost</h3>
                            <canvas id="modelChart"></canvas>
                        </div>
                    </div>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>Model</th>
                                <th>Sessions</th>
                                <th>Input Tokens</th>
                                <th>Output Tokens</th>
                                <th>Cost</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${Object.entries(data.by_model || {}).slice(0, 10).map(([model, d]) => `
                                <tr>
                                    <td>${model.substring(0, 40)}</td>
                                    <td>${d.sessions || 0}</td>
                                    <td>${d.input_tokens_formatted || '0'}</td>
                                    <td>${d.output_tokens_formatted || '0'}</td>
                                    <td>${d.calculated_cost_formatted || '$0.00'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
                
                document.getElementById('timestamp').textContent = 'Last updated: ' + (data.timestamp || '');
                
                // Charts
                if (data.daily_labels) {
                    new Chart(document.getElementById('dailyChart'), {
                        type: 'line',
                        data: {
                            labels: data.daily_labels,
                            datasets: [{ label: 'Cost ($)', data: data.daily_costs, 
                                        borderColor: '#00d4ff', backgroundColor: 'rgba(0,212,255,0.1)',
                                        fill: true, tension: 0.4 }]
                        },
                        options: { responsive: true, maintainAspectRatio: false,
                                  plugins: { legend: { display: false } },
                                  scales: { x: { ticks: { color: '#666' }, grid: { color: '#2a2a4e' } },
                                           y: { ticks: { color: '#666' }, grid: { color: '#2a2a4e' } } } }
                    });
                }
                
                if (data.model_names) {
                    new Chart(document.getElementById('modelChart'), {
                        type: 'bar',
                        data: {
                            labels: data.model_names,
                            datasets: [{ label: 'Cost ($)', data: data.model_costs,
                                        backgroundColor: '#00d4ff' }]
                        },
                        options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y',
                                  plugins: { legend: { display: false } },
                                  scales: { x: { ticks: { color: '#666' }, grid: { color: '#2a2a4e' } },
                                           y: { ticks: { color: '#666' }, grid: { display: false } } } }
                    });
                }
            } catch (e) {
                document.getElementById('content').innerHTML = 
                    '<div class="error"><h2>Error</h2><p>Failed to load dashboard</p></div>';
            }
        }
        loadDashboard();
    </script>
</body>
</html>
    """
    return html

@app.route("/api/summary")
@auth.login_required
def api_summary():
    """JSON API for summary data."""
    data = fetch_from_gist()
    if "error" in data:
        # Return mock data if gist not configured
        data = {
            "total_sessions": 0,
            "total_calculated_cost": 0,
            "total_calculated_cost_formatted": "$0.00",
            "total_tokens_formatted": "0",
            "avg_daily_cost": 0,
            "avg_daily_cost_formatted": "$0.00",
            "by_model": {},
            "daily_labels": [],
            "daily_costs": [],
            "model_names": [],
            "model_costs": [],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    # Ensure required fields
    required = ["total_sessions", "total_calculated_cost", "total_tokens_formatted",
               "total_calculated_cost_formatted", "avg_daily_cost_formatted",
               "by_model", "timestamp", "daily_labels", "daily_costs",
               "model_names", "model_costs"]
    
    for field in required:
        if field not in data:
            data[field] = {} if field == "by_model" else []
    
    return jsonify(data)

@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

# Vercel handler
def handler(request):
    return app(request.environ, lambda status, headers: response(status, headers))

# For local development
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)