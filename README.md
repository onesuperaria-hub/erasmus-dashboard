# Erasmus Dashboard

**Live cost tracking dashboard for Hermes Agent** – Monitor LLM usage, spending trends, and system metrics.

![Dashboard Preview](https://img.shields.io/badge/status-production%20ready-green)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

**Public Repository:** https://github.com/onesuperaria-hub/erasmus-dashboard

## ✨ Features

### ✅ **Live Cost Tracking**
- Real-time LLM usage cost analysis from Hermes `state.db`
- Model-level breakdown (DeepSeek, Claude, Gemini, etc.)
- Daily/weekly/monthly spending trends
- Top cost offenders identification

### ✅ **Secure & Private**
- HTTP Basic Authentication (password protected)
- Data stays private (GitHub Gist sync or local-only)
- No third-party analytics

### ✅ **Cloud Ready**
- Single-page design (fits browser window, no scrolling)
- Responsive charts with fixed heights
- Deploys in 5 minutes to Railway/Render

### 📊 **Dashboard Preview**
- **Total Sessions & Cost** – Overview of all usage
- **Daily Spending Chart** – 7-day trend visualization  
- **Top Models Table** – Sorted by cost, scrollable view
- **Timestamp** – Last data refresh time

## 🚀 Quick Deploy

### **Option 1: Railway (Recommended)**
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/w2Dc6r?referralCode=public)

1. Click the button above
2. Sign in with GitHub
3. Set environment variables:
   - `DASHBOARD_USER` – Your username
   - `DASHBOARD_PASSWORD` – Secure password
   - `GIST_ID` – (from step below)
   - `GITHUB_TOKEN` – Token with `gist` scope
   - `LOCAL_MODE` – `false`
4. Deploy!

### **Option 2: Render**
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/onesuperaria-hub/erasmus-dashboard)

1. Click the button above
2. Connect GitHub account
3. Set same environment variables as above
4. Deploy!

## 📋 Pre-Deployment Setup

### **Step 1: Create GitHub Token**
1. Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. Click **"Generate new token (classic)"**
3. Select **`gist` scope** (✓)
4. Copy the token

### **Step 2: Create Data Gist**
```bash
# Clone the repository
git clone https://github.com/onesuperaria-hub/erasmus-dashboard
cd erasmus-dashboard

# Create Gist with your cost data
GITHUB_TOKEN='your_token_here' python3 sync_to_gist.py
```

The script will:
- Read your local `~/.hermes/state.db`
- Generate cost summary
- Create a private GitHub Gist
- Output `GIST_ID=...` (save this!)

### **Step 3: Deploy**
Use one of the deploy buttons above, or manually:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway variables set DASHBOARD_USER='your_username'
railway variables set DASHBOARD_PASSWORD='secure_password'
railway variables set GIST_ID='your_gist_id'
railway variables set GITHUB_TOKEN='your_github_token'
railway variables set LOCAL_MODE='false'
railway up
```

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DASHBOARD_USER` | Yes | Username for HTTP Basic Auth |
| `DASHBOARD_PASSWORD` | Yes | Password for HTTP Basic Auth |
| `LOCAL_MODE` | No | `true` for local SQLite, `false` for Gist (cloud) |
| `GIST_ID` | Cloud only | GitHub Gist ID containing JSON data |
| `GITHUB_TOKEN` | Cloud only | GitHub token with `gist` scope |
| `PORT` | No | Port to bind (default: 5000) |

## 🖥️ Local Development

```bash
# Clone repository
git clone https://github.com/onesuperaria-hub/erasmus-dashboard
cd erasmus-dashboard

# Install dependencies
pip install -r requirements.txt

# Run local dashboard (no auth)
python3 app.py
# Open http://localhost:5000

# Run with authentication
export DASHBOARD_USER='admin'
export DASHBOARD_PASSWORD='secure_pass'
export LOCAL_MODE='true'
python3 app_cloud.py
# Open http://localhost:5001 (login required)
```

## 📁 Project Structure

```
erasmus-dashboard/
├── app.py                    # Original local dashboard (no auth)
├── app_cloud.py              # Production app with authentication
├── sync_to_gist.py           # Data sync to GitHub Gist
├── deploy_railway.py         # Railway deployment helper
├── requirements.txt          # Python dependencies
├── Procfile                  # Railway/Render process file
├── railway.toml              # Railway configuration
├── render.yaml               # Render configuration
├── runtime.txt               # Python version
├── DEPLOYMENT.md             # Detailed deployment guide
├── .env.example              # Environment template
├── templates/
│   └── index.html            # Dashboard UI (single-page design)
└── utils/
    └── cost_tracker.py       # Hermes DB parsing and cost calculation
```

## 🔄 Automated Data Sync

For cloud deployment, set up a cron job to sync data hourly:

```bash
# Edit crontab
crontab -e

# Add line (adjust paths)
0 * * * * cd /path/to/erasmus-dashboard && \
  GITHUB_TOKEN='your_token' \
  GIST_ID='your_gist_id' \
  python3 sync_to_gist.py >> ~/dashboard_sync.log 2>&1
```

## 🛠️ Technical Details

### **Data Flow**
1. **Local:** Hermes Agent writes to `~/.hermes/state.db`
2. **Sync:** `sync_to_gist.py` reads DB, creates/updates private Gist
3. **Cloud:** Dashboard reads JSON from Gist via GitHub API
4. **UI:** Single-page dashboard displays charts and tables

### **Authentication**
- HTTP Basic Auth via Flask-HTTPAuth
- Passwords hashed with PBKDF2-SHA256
- No sessions or cookies – stateless

### **UI Design**
- Fixed height charts (250px) – no infinite scrolling
- Scrollable tables (max-height: 350px)
- Uses `vh` units for responsive sizing
- Chart.js for visualization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Submit a pull request

## 📄 License

MIT License – see [LICENSE](LICENSE) file.

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/onesuperaria-hub/erasmus-dashboard/issues)
- **Telegram:** @Erebus_the_bot (for alerts)

---

**Built by Hermes Agent for Sean Wright** – Cost tracking made simple.