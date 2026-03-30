# Erasmus Dashboard Deployment Guide

Two deployment options:

1. **Cloud Deployment (Recommended)** – Host on Railway/Render with GitHub Gist sync
2. **Local + Secure Tunnel** – Keep data local, add authentication, expose via ngrok

## Option 1: Cloud Deployment (Railway)

### Prerequisites
1. GitHub account with a [Personal Access Token](https://github.com/settings/tokens) with `gist` scope
2. Railway account (railway.app) or Render account

### Step 1: Create GitHub Gist for Data Sync
The dashboard reads cost data from a private GitHub Gist. You'll sync data from your local machine periodically.

```bash
# Install dependencies
cd /Users/erasamus/DEV\ PROJECTS/erasmus-dashboard
pip3 install -r requirements.txt

# Set your GitHub token (replace with your actual token)
export GITHUB_TOKEN="ghp_..."

# Run sync script to create initial gist
python3 sync_to_gist.py
```

The script will:
- Generate summary JSON from your local `~/.hermes/state.db`
- Create a private GitHub Gist
- Output the Gist ID (save this for next step)

### Step 2: Deploy to Railway

**Method A: CLI Deployment**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link to existing project or create new
railway link

# Set environment variables
railway variables set DASHBOARD_USER="your_username"
railway variables set DASHBOARD_PASSWORD="secure_password"
railway variables set GIST_ID="your_gist_id_from_step1"
railway variables set GITHUB_TOKEN="your_github_token"
railway variables set LOCAL_MODE="false"

# Deploy
railway up
```

**Method B: Web Dashboard**
1. Push code to GitHub repository
2. Go to [Railway](https://railway.app)
3. Create new project → Deploy from GitHub repo
4. Add environment variables (see `.env.example`)
5. Deploy

### Step 3: Configure Automated Sync
Set up a cron job to sync data hourly:

```bash
# Edit crontab
crontab -e

# Add line (adjust paths and token)
0 * * * * cd /Users/erasamus/DEV\ PROJECTS/erasmus-dashboard && GITHUB_TOKEN="your_token" GIST_ID="your_gist_id" python3 sync_to_gist.py >> ~/dashboard_sync.log 2>&1
```

## Option 2: Local + Secure Tunnel

Keep dashboard running locally with authentication, expose via secure tunnel.

### Step 1: Add Authentication to Local Dashboard
The `app_cloud.py` already includes HTTP Basic Auth. Run it locally:

```bash
cd /Users/erasamus/DEV\ PROJECTS/erasmus-dashboard

# Set auth credentials
export DASHBOARD_USER="your_username"
export DASHBOARD_PASSWORD="secure_password"
export LOCAL_MODE="true"

# Run with auth
python3 app_cloud.py
```

Access at: http://localhost:5000 (login with credentials above)

### Step 2: Expose via Secure Tunnel
Use ngrok for temporary public access:

```bash
# Install ngrok (brew install ngrok/ngrok/ngrok)
ngrok authtoken your_ngrok_token
ngrok http 5000
```

Permanent solution: Use Cloudflare Tunnel, Tailscale, or SSH reverse tunnel.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DASHBOARD_USER` | Yes | Username for HTTP Basic Auth |
| `DASHBOARD_PASSWORD` | Yes | Password for HTTP Basic Auth |
| `LOCAL_MODE` | No | `true` for local SQLite, `false` for Gist (cloud) |
| `GIST_ID` | Cloud only | GitHub Gist ID containing JSON data |
| `GITHUB_TOKEN` | Cloud only | GitHub token with gist scope |
| `PORT` | No | Port to bind (default: 5000) |

## Security Notes

1. **Always use strong passwords** – The dashboard exposes cost data
2. **GitHub token** – Use fine-grained token with only `gist` scope
3. **HTTPS** – Railway/Render provide HTTPS automatically
4. **Regular updates** – Keep dependencies updated
5. **Monitor access logs** – Check for unauthorized attempts

## Troubleshooting

### Cloud deployment shows "No data"
- Verify GIST_ID and GITHUB_TOKEN are correct
- Run sync script locally to ensure gist contains data
- Check Railway logs: `railway logs`

### Authentication fails
- Ensure DASHBOARD_USER and DASHBOARD_PASSWORD are set
- Password should not contain special characters that break shell

### Local mode fails to find database
- Ensure Hermes is installed and `~/.hermes/state.db` exists
- Run locally with `LOCAL_MODE=true`

## Files Overview

- `app_cloud.py` – Cloud-optimized Flask app with auth
- `app.py` – Original local-only app
- `sync_to_gist.py` – Data synchronization script
- `Procfile`, `runtime.txt` – Deployment configuration
- `railway.toml` – Railway deployment config
- `.env.example` – Environment variable template

## Next Steps After Deployment

1. Set up cron for hourly data sync
2. Configure Telegram alerts for cost thresholds
3. Add more dashboard features (system monitoring, logs viewer)
4. Implement rate limiting
5. Add audit logging