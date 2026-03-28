# MiroFish — Deployment Guide

Step-by-step instructions for deploying MiroFish (including the ski dashboard) using **100% free** hosting options.

---

## Cost Summary

| Service | Cost | Notes |
|---------|------|-------|
| Weather API (Open-Meteo) | **FREE** | No key, no limits |
| Webcams | **FREE** | Public resort embeds |
| Hosting — Render | **FREE** | 750 hrs/month (~24/7 for 1 service) |
| Hosting — Fly.io | **FREE** | $0/month on free tier |
| Database | **FREE** | SQLite (bundled) |
| CI/CD (GitHub Actions) | **FREE** | Public repos |
| **Total** | **$0/month** | No credit card required |

---

## Option A — Deploy to Render (Recommended)

Render offers a generous free tier and native GitHub integration.

### Step 1 — Push to GitHub

Ensure your code is pushed to the `main` branch of your GitHub repository.

### Step 2 — Create a Render Account

Sign up at [https://render.com](https://render.com) — no credit card required.

### Step 3 — Create a New Web Service

1. Click **New → Web Service**
2. Connect your GitHub account and select the `NightDread06/mirofish` repository
3. Configure:
   - **Name**: `mirofish-backend`
   - **Environment**: `Python 3`
   - **Build command**: `pip install -r backend/requirements.txt`
   - **Start command**: `cd backend && python run.py`
4. Add environment variables (under **Environment**):

   | Key | Value |
   |-----|-------|
   | `FLASK_ENV` | `production` |
   | `WEATHER_API` | `open-meteo` |
   | `AVORIAZ_LAT` | `46.3627` |
   | `AVORIAZ_LON` | `6.6330` |
   | `REFRESH_INTERVAL_MINUTES` | `10` |
   | `SECRET_KEY` | *(generate a random string)* |
   | `LLM_API_KEY` | *(your LLM key)* |
   | `ZEP_API_KEY` | *(your Zep key)* |

5. Click **Create Web Service**

### Step 4 — Auto-deploy on Push

Set up the GitHub Actions workflow for automatic deployment:

1. Go to your Render service → **Settings → Deploy Hook**
2. Copy the deploy hook URL
3. In GitHub: **Settings → Secrets → Actions → New repository secret**
   - Name: `RENDER_DEPLOY_HOOK`
   - Value: *(paste the URL)*

Now every push to `main` will trigger a Render re-deployment via `.github/workflows/deploy-render.yml`.

### Step 5 — Access Your Dashboard

Your backend will be live at:
```
https://mirofish-backend.onrender.com
```

Ski dashboard endpoints:
```
https://mirofish-backend.onrender.com/api/ski/weather/current
https://mirofish-backend.onrender.com/api/ski/conditions
https://mirofish-backend.onrender.com/api/ski/recommendations
```

> **Note**: Render free tier services spin down after 15 minutes of inactivity.  
> The first request after sleep may take ~30 seconds to respond.

---

## Option B — Deploy to Fly.io (Always-On Alternative)

Fly.io provides a free tier with persistent machines that don't sleep.

### Step 1 — Install Fly CLI

```bash
# macOS / Linux
curl -L https://fly.io/install.sh | sh

# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex
```

### Step 2 — Sign In

```bash
flyctl auth login
```

No credit card required for the free tier.

### Step 3 — Launch the App

```bash
flyctl launch
```

This reads `fly.toml` and configures the app. When prompted:
- **App name**: `mirofish` (or your preferred name)
- **Region**: `cdg` (Paris — closest to Avoriaz)
- **PostgreSQL**: No (SQLite is used by default)

### Step 4 — Set Secrets

```bash
flyctl secrets set \
  FLASK_ENV=production \
  SECRET_KEY=your-random-secret \
  LLM_API_KEY=your-llm-key \
  ZEP_API_KEY=your-zep-key
```

### Step 5 — Deploy

```bash
flyctl deploy
```

### Step 6 — Auto-deploy via GitHub Actions

1. Get your Fly.io API token:
   ```bash
   flyctl tokens create deploy -x 999999h
   ```
2. Add it as a GitHub secret named `FLY_API_TOKEN`

Now every push to `main` triggers `.github/workflows/deploy-flyio.yml`.

### Step 7 — Access Your App

```bash
flyctl open
```

---

## Option C — Docker (Self-Hosted / VPS)

For running on your own server or a VPS.

### Prerequisites

- Docker & Docker Compose installed
- Ports 3000 and 5001 open on the server

### Deploy

```bash
# 1. Clone the repository on your server
git clone https://github.com/NightDread06/mirofish.git
cd mirofish

# 2. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 3. Start with Docker Compose
docker-compose up -d

# 4. View logs
docker-compose logs -f
```

The app will be available at `http://your-server-ip:3000` (frontend) and `http://your-server-ip:5001` (backend API).

---

## Continuous Deployment Summary

| Platform | Trigger | Workflow file |
|----------|---------|---------------|
| Render | Push to `main` | `.github/workflows/deploy-render.yml` |
| Fly.io | Push to `main` | `.github/workflows/deploy-flyio.yml` |
| Docker | Manual / cron | `docker-compose.yml` |

---

## Monitoring

### Check backend health

```
GET /health
```

### Check ski scheduler status

```
GET /api/ski/scheduler/status
```

### Force weather + camera refresh

```
GET /api/ski/scheduler/refresh
```

---

## Troubleshooting

### Render: "No open ports detected"

Ensure `run.py` binds to `0.0.0.0` and reads `PORT` from the environment:

```python
port = int(os.environ.get('PORT', os.environ.get('FLASK_PORT', 5001)))
app.run(host='0.0.0.0', port=port)
```

### Fly.io: "Error: app not found"

Run `flyctl launch` first to create the app, then `flyctl deploy`.

### Scheduler jobs not running

Verify APScheduler is installed and the `/api/ski/scheduler/status` endpoint shows `"running": true`.
