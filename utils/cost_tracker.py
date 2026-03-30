"""
Cost tracking utilities for Hermes Agent.
Reads from ~/.hermes/state.db and calculates usage costs.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# Model pricing (cost per token in USD)
# Based on OpenRouter pricing as of March 2026
MODEL_PRICING = {
    "deepseek/deepseek-v3.2": {
        "input": 0.14e-6,
        "output": 0.28e-6,
        "reasoning": 0.14e-6,
        "cache_read": 0.0,
        "cache_write": 0.0
    },
    "deepseek/deepseek-chat-v3-0324": {
        "input": 0.14e-6,
        "output": 0.28e-6,
        "reasoning": 0.14e-6,
        "cache_read": 0.0,
        "cache_write": 0.0
    },
    "claude-haiku-4-5-20251001": {
        "input": 0.08e-6,
        "output": 0.24e-6,
        "reasoning": 0.08e-6,
        "cache_read": 0.0,
        "cache_write": 0.0
    },
    "qwen2.5:3b": {
        "input": 0.0,
        "output": 0.0,
        "reasoning": 0.0,
        "cache_read": 0.0,
        "cache_write": 0.0
    },
    "anthropic/claude-sonnet-4": {
        "input": 3.0e-6,
        "output": 15.0e-6,
        "reasoning": 3.0e-6,
        "cache_read": 0.0,
        "cache_write": 0.0
    },
    "google/gemini-2.5-flash": {
        "input": 0.075e-6,
        "output": 0.3e-6,
        "reasoning": 0.075e-6,
        "cache_read": 0.0,
        "cache_write": 0.0
    },
}

def get_db_path() -> Optional[Path]:
    """Get path to Hermes state database."""
    home = Path.home()
    db_path = home / ".hermes" / "state.db"
    if not db_path.exists():
        return None
    return db_path

def calculate_cost(model: str, input_tokens: int, output_tokens: int,
                   reasoning_tokens: int = 0, cache_read_tokens: int = 0,
                   cache_write_tokens: int = 0) -> float:
    """Calculate cost based on model pricing."""
    if not model:
        model = "unknown"
    if model in MODEL_PRICING:
        pricing = MODEL_PRICING[model]
        input_cost = input_tokens * pricing["input"]
        output_cost = output_tokens * pricing["output"]
        reasoning_cost = reasoning_tokens * pricing.get("reasoning", pricing["input"])
        cache_read_cost = cache_read_tokens * pricing.get("cache_read", 0.0)
        cache_write_cost = cache_write_tokens * pricing.get("cache_write", 0.0)
        return input_cost + output_cost + reasoning_cost + cache_read_cost + cache_write_cost
    else:
        # Default fallback pricing
        return (input_tokens + reasoning_tokens) * 0.3e-6 + output_tokens * 0.6e-6

def get_sessions_summary(db_path: Path, days_back: int = 30) -> Dict[str, Any]:
    """Get summary of sessions from database."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all sessions within time period
    cutoff_time = datetime.now() - timedelta(days=days_back)
    cutoff_timestamp = cutoff_time.timestamp()
    
    query = """
    SELECT 
        id,
        model,
        input_tokens,
        output_tokens,
        reasoning_tokens,
        cache_read_tokens,
        cache_write_tokens,
        started_at,
        estimated_cost_usd,
        actual_cost_usd
    FROM sessions 
    WHERE started_at >= ?
    ORDER BY started_at DESC
    """
    
    cursor.execute(query, (cutoff_timestamp,))
    rows = cursor.fetchall()
    
    summary = {
        "total_sessions": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_reasoning_tokens": 0,
        "total_cache_read_tokens": 0,
        "total_cache_write_tokens": 0,
        "total_estimated_cost": 0.0,
        "total_actual_cost": 0.0,
        "total_calculated_cost": 0.0,
        "by_model": {},
        "by_day": {},
    }
    
    for row in rows:
        model = row["model"]
        input_tokens = row["input_tokens"] or 0
        output_tokens = row["output_tokens"] or 0
        reasoning_tokens = row["reasoning_tokens"] or 0
        cache_read_tokens = row["cache_read_tokens"] or 0
        cache_write_tokens = row["cache_write_tokens"] or 0
        estimated = row["estimated_cost_usd"] or 0.0
        actual = row["actual_cost_usd"] or 0.0
        
        # Calculate our own cost estimate
        calculated = calculate_cost(model, input_tokens, output_tokens,
                                   reasoning_tokens, cache_read_tokens, cache_write_tokens)
        
        # Update totals
        summary["total_sessions"] += 1
        summary["total_input_tokens"] += input_tokens
        summary["total_output_tokens"] += output_tokens
        summary["total_reasoning_tokens"] += reasoning_tokens
        summary["total_cache_read_tokens"] += cache_read_tokens
        summary["total_cache_write_tokens"] += cache_write_tokens
        summary["total_estimated_cost"] += estimated
        summary["total_actual_cost"] += actual
        summary["total_calculated_cost"] += calculated
        
        # By model
        if model not in summary["by_model"]:
            summary["by_model"][model] = {
                "sessions": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "reasoning_tokens": 0,
                "calculated_cost": 0.0,
            }
        
        summary["by_model"][model]["sessions"] += 1
        summary["by_model"][model]["input_tokens"] += input_tokens
        summary["by_model"][model]["output_tokens"] += output_tokens
        summary["by_model"][model]["reasoning_tokens"] += reasoning_tokens
        summary["by_model"][model]["calculated_cost"] += calculated
        
        # By day
        session_date = datetime.fromtimestamp(row["started_at"]).strftime("%Y-%m-%d")
        if session_date not in summary["by_day"]:
            summary["by_day"][session_date] = {
                "sessions": 0,
                "calculated_cost": 0.0,
            }
        
        summary["by_day"][session_date]["sessions"] += 1
        summary["by_day"][session_date]["calculated_cost"] += calculated
    
    conn.close()
    return summary

def format_currency(amount: float) -> str:
    """Format currency amount."""
    if amount < 0.01:
        return f"${amount:.4f}"
    elif amount < 1:
        return f"${amount:.3f}"
    else:
        return f"${amount:.2f}"

def format_tokens(tokens: int) -> str:
    """Format token count."""
    if tokens >= 1_000_000:
        return f"{tokens/1_000_000:.2f}M"
    elif tokens >= 1_000:
        return f"{tokens/1_000:.1f}K"
    else:
        return str(tokens)

def get_daily_costs_last_n_days(db_path: Path, days: int = 7) -> List[Dict]:
    """Get daily cost data for the last N days."""
    summary = get_sessions_summary(db_path, days_back=days)
    days_data = []
    today = datetime.now()
    for i in range(days - 1, -1, -1):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        if date in summary["by_day"]:
            days_data.append({
                "date": date,
                "sessions": summary["by_day"][date]["sessions"],
                "cost": summary["by_day"][date]["calculated_cost"]
            })
        else:
            days_data.append({
                "date": date,
                "sessions": 0,
                "cost": 0.0
            })
    return days_data