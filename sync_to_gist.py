#!/usr/bin/env python3
"""
Sync Hermes cost data to GitHub Gist for cloud dashboard.
Run this periodically via cron to keep cloud data updated.
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
import requests

# Configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GIST_ID = os.environ.get('GIST_ID')  # Leave empty to create new gist
GIST_FILENAME = "hermes_cost_summary.json"
GIST_DESCRIPTION = "Hermes Agent Cost Dashboard Data"

def get_summary_data():
    """Generate summary JSON using local cost tracker."""
    try:
        # Add utils to path
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
        return {"error": f"Import failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to generate summary: {str(e)}"}

def create_or_update_gist(data):
    """Create or update GitHub Gist with summary data."""
    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN not set")
        return None
    
    url = "https://api.github.com/gists"
    if GIST_ID:
        url = f"{url}/{GIST_ID}"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    payload = {
        "description": GIST_DESCRIPTION,
        "public": False,
        "files": {
            GIST_FILENAME: {
                "content": json.dumps(data, indent=2)
            }
        }
    }
    
    try:
        if GIST_ID:
            # Update existing gist
            resp = requests.patch(url, headers=headers, json=payload, timeout=30)
            action = "updated"
        else:
            # Create new gist
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            action = "created"
        
        if resp.status_code in [200, 201]:
            result = resp.json()
            gist_id = result["id"]
            gist_url = result["html_url"]
            print(f"✅ Gist {action}: {gist_url}")
            print(f"   ID: {gist_id}")
            
            # Save GIST_ID to .env for future use
            if not GIST_ID:
                env_path = Path.home() / ".hermes" / ".env"
                if env_path.exists():
                    with open(env_path, "r") as f:
                        content = f.read()
                    if "GIST_ID=" not in content:
                        with open(env_path, "a") as f:
                            f.write(f"\nGIST_ID={gist_id}\n")
                        print(f"   Saved GIST_ID to {env_path}")
            
            return gist_id
        else:
            print(f"❌ GitHub API error: {resp.status_code}")
            print(f"   Response: {resp.text[:500]}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to sync to gist: {e}")
        return None

def main():
    print("🔄 Syncing Hermes cost data to GitHub Gist...")
    
    # Get summary data
    print("📊 Generating cost summary...")
    data = get_summary_data()
    if "error" in data:
        print(f"❌ {data['error']}")
        sys.exit(1)
    
    print(f"✅ Summary generated: {data['total_sessions']} sessions, ${data['total_calculated_cost']:.4f} total")
    
    # Sync to gist
    print("☁️  Uploading to GitHub Gist...")
    gist_id = create_or_update_gist(data)
    
    if gist_id:
        print(f"✅ Sync complete!")
        print(f"   Next: Set GIST_ID={gist_id} in cloud deployment environment")
    else:
        print("❌ Sync failed")
        sys.exit(1)

if __name__ == "__main__":
    main()