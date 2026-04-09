# MiroFish — Ski Dashboard Setup Guide

This guide covers local development setup and environment configuration for the MiroFish ski dashboard feature, which provides live Avoriaz/Portes du Soleil conditions, weather forecasts, webcam feeds, and automated recommendations.

---

## Prerequisites

| Tool | Minimum version |
|------|----------------|
| Python | 3.11+ |
| Node.js | 18+ |
| npm | 9+ |
| uv (optional) | any |

---

## 1. Clone & Install

```bash
git clone https://github.com/NightDread06/mirofish.git
cd mirofish

# Install all dependencies (Node root + frontend + Python backend)
npm run setup:all
```

---

## 2. Environment Configuration

```bash
cp .env.example .env
```

Open `.env` and fill in the required values:

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_API_KEY` | Yes | OpenAI-compatible LLM API key |
| `ZEP_API_KEY` | Yes | Zep Cloud memory API key |
| `WEATHER_API` | No | `open-meteo` (default, free, no key needed) |
| `AVORIAZ_LAT` | No | Resort latitude (default `46.3627`) |
| `AVORIAZ_LON` | No | Resort longitude (default `6.6330`) |
| `WEBCAM_SOURCES` | No | JSON array of webcam sources |
| `REFRESH_INTERVAL_MINUTES` | No | Scheduler interval (default `10`) |
| `CACHE_TTL_SECONDS` | No | Cache lifetime in seconds (default `600`) |
| `SECRET_KEY` | No | Flask secret key (change in production) |
| `VITE_API_BASE_URL` | No | Backend URL for frontend (default `http://localhost:5001/api`) |

---

## 3. Weather API Setup (Open-Meteo — No Sign-up Required)

The ski dashboard uses [Open-Meteo](https://open-meteo.com/) by default.

- ✅ **Free forever** — no API key, no credit card
- ✅ Provides temperature, snowfall, snow depth, wind speed, visibility
- ✅ 7–16 day forecast including ski-relevant variables

To verify connectivity:

```bash
curl "https://api.open-meteo.com/v1/forecast?latitude=46.3627&longitude=6.6330&hourly=temperature_2m,snowfall,snow_depth&forecast_days=1"
```

You should receive a JSON response with hourly weather data.

---

## 4. Webcam Source Configuration

Webcam sources are configured via the `WEBCAM_SOURCES` environment variable as a JSON array:

```json
[
  {"name": "Avoriaz Official", "url": "https://www.avoriaz.com/en/webcams/", "type": "embed"},
  {"name": "Bergfex Avoriaz",  "url": "https://www.bergfex.com/avoriaz/webcams/c35/", "type": "iframe"},
  {"name": "Portes du Soleil", "url": "https://www.portesdusoleil.com/en/webcams/", "type": "embed"}
]
```

Each entry supports these `type` values:
- `embed` — render in an `<embed>` or `<iframe>` on the dashboard
- `iframe` — render in a standalone `<iframe>`
- `image` — direct image URL refreshed periodically
- `stream` — direct MJPEG/HLS stream URL

---

## 5. Running Locally

```bash
# Start both backend (port 5001) and frontend (port 3000) simultaneously
npm run dev
```

The frontend proxy is pre-configured to forward `/api/*` requests to `http://localhost:5001`.

Individual services:

```bash
# Backend only
npm run backend

# Frontend only
npm run frontend
```

---

## 6. Ski Dashboard API Endpoints

Once the backend is running, the following endpoints are available:

| Endpoint | Description |
|----------|-------------|
| `GET /api/ski/weather/current` | Current conditions at Avoriaz |
| `GET /api/ski/weather/hourly?hours=24` | Hourly forecast |
| `GET /api/ski/weather/daily?days=8` | Daily forecast |
| `GET /api/ski/cameras` | List configured webcam sources |
| `GET /api/ski/conditions?time=<ISO>` | All run conditions |
| `GET /api/ski/recommendations` | Top 3 recommended runs |
| `GET /api/ski/day-plan` | Hour-by-hour itinerary |
| `GET /api/ski/hidden-gems` | Off-the-beaten-path suggestions |
| `GET /api/ski/stress-test` | Adversarial scenario analysis |
| `GET /api/ski/forecast` | Combined weather summary |
| `GET /api/ski/scheduler/status` | Scheduler health check |
| `GET /api/ski/scheduler/refresh` | Force immediate refresh |

---

## 7. Background Scheduler

The ski dashboard automatically refreshes data in the background:

- **Every 10 minutes** — weather data (configurable via `REFRESH_INTERVAL_MINUTES`)
- **Every 30 minutes** — webcam status checks
- **Every 60 minutes** — expired cache cleanup

The scheduler starts automatically when the Flask backend starts.  
Check scheduler status: `GET /api/ski/scheduler/status`  
Force a manual refresh: `GET /api/ski/scheduler/refresh`

---

## 8. Docker (Local Development)

```bash
# Build and start using Docker Compose
docker-compose up --build

# Stop
docker-compose down
```

The container exposes ports `3000` (frontend) and `5001` (backend).

---

## 9. Troubleshooting

### Backend won't start — `LLM_API_KEY` or `ZEP_API_KEY` not configured

The main MiroFish platform requires these keys. Add them to your `.env` file.  
The ski dashboard endpoints themselves do **not** require LLM or Zep keys.

### Weather data shows "simulated" source

The Open-Meteo API is unreachable. Check your internet connection or firewall.  
The backend will automatically fall back to plausible simulated data.

### Scheduler not starting

Ensure `APScheduler` is installed:

```bash
cd backend && pip install APScheduler>=3.10.0
```

### Webcam status shows "unknown"

Webcam status is only probed during scheduled refreshes (every 30 min) to avoid slow API responses.  
Trigger an immediate check: `GET /api/ski/scheduler/refresh`
