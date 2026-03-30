# Erasmus Home Page Dashboard

A centralized dashboard for monitoring Hermes Agent usage costs, system metrics, and operational status.

## Features

### Phase 1: Cost Tracking
- Real-time LLM usage cost analysis from Hermes state.db
- Model-level breakdown (DeepSeek, Claude, Gemini, etc.)
- Daily/weekly/monthly spending trends
- Cost forecasting

### Phase 2: System Monitoring
- CPU, memory, disk usage
- Network activity
- Service status (gateway, cron, etc.)
- Log monitoring

### Phase 3: Integrations
- Telegram bot status
- GitHub activity
- Automated reports

## Tech Stack
- **Backend**: Python (Flask/FastAPI)
- **Frontend**: HTMX + Tailwind CSS (simple, server-rendered)
- **Database**: SQLite (Hermes state.db read-only)
- **Charts**: Chart.js or Plotly
- **Deployment**: Local web server, optionally Docker

## Project Structure
```
erasmus-dashboard/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── static/               # CSS, JS, images
├── templates/            # HTML templates
├── utils/
│   ├── cost_tracker.py   # Cost analysis from Hermes DB
│   └── system_monitor.py # System metrics collection
├── tests/
└── README.md
```

## Getting Started

1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure path to Hermes state.db (default: ~/.hermes/state.db)
4. Run: `python app.py`
5. Open http://localhost:5000

## Data Sources
- `~/.hermes/state.db`: Session history, token counts, costs
- System metrics: psutil, platform
- Telegram gateway logs

## License
MIT