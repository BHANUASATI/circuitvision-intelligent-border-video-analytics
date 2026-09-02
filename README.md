# IBVAP — Intelligent Border Video Analytics Platform

> **Team Circuit Crew · SIH 2026**
> GitHub: https://github.com/BHANUASATI/circuitvision-intelligent-border-video-analytics

AI-driven software platform that transforms existing CCTV infrastructure into an intelligent surveillance network — no dedicated hardware required.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Nginx (443 / 80)                    │
│          TLS termination · Rate limiting · WebSocket proxy  │
└──────────┬─────────────────┬──────────────────┬────────────┘
           │                 │                  │
    ┌──────▼──────┐  ┌───────▼───────┐  ┌──────▼──────┐
    │   Frontend  │  │    Backend    │  │ AI Service  │
    │  React + TS │  │   FastAPI     │  │  FastAPI    │
    │  Vite + TW  │  │   Port 8000   │  │  Port 8001  │
    └─────────────┘  └───────┬───────┘  └──────┬──────┘
                             │                  │
                    ┌────────▼─────────┐        │
                    │   PostgreSQL 16  │        │
                    │   Redis 7        │◄───────┘
                    └──────────────────┘    (pub/sub alerts)
```

## Features

| Capability | Technology |
|---|---|
| Human & vehicle detection | YOLOv8 (ultralytics) |
| Multi-object tracking | ByteTrack (inline implementation) |
| Automatic Number Plate Recognition | YOLO + EasyOCR |
| Face detection & recognition | InsightFace (buffalo_l) |
| Virtual fence intrusion detection | Shapely polygon/line geometry |
| Activity detection (loitering, running, crowding, night movement) | Trajectory analysis |
| Real-time alert push | WebSocket + Redis pub/sub |
| Evidence integrity | SHA-256 tamper-evident hashing |
| Auth & access control | JWT + RBAC roles |
| Audit trail | Immutable audit_logs table |
| Stream ingestion | RTSP via OpenCV/FFmpeg |

## Quick Start

```bash
# Clone
git clone https://github.com/BHANUASATI/circuitvision-intelligent-border-video-analytics.git
cd ibvap

# Setup (generates certs, seeds DB, builds images)
bash scripts/setup_dev.sh

# Start everything
docker compose up -d

# Open dashboard
open https://localhost
# Login: admin / Admin@1234
```

## Project Structure

```
ibvap/
├── ai_service/          # Python CV/AI microservice (YOLO, tracking, ANPR, face rec)
│   ├── core/            # Stream worker & manager
│   ├── modules/         # detection, tracking, anpr, face_recognition, intrusion, activity
│   ├── api/             # FastAPI routes
│   └── utils/           # evidence hashing, redis, logger
├── backend/             # FastAPI REST API + WebSocket
│   ├── app/
│   │   ├── api/v1/      # auth, cameras, alerts, incidents, analytics, websocket
│   │   ├── models/      # SQLAlchemy ORM models
│   │   ├── schemas/     # Pydantic v2 schemas
│   │   └── services/    # business logic layer
│   └── migrations/      # Alembic migrations
├── frontend/            # React + TypeScript + Tailwind dashboard
│   └── src/
│       ├── pages/       # Dashboard, Cameras, Alerts, Incidents, Analytics, Users
│       ├── components/  # Layout, Sidebar, AlertFeed, charts
│       ├── store/       # Redux slices (auth, alerts, cameras, ui)
│       └── api/         # Axios client + endpoint wrappers
├── nginx/               # Reverse proxy + TLS config
├── scripts/             # init_db.sql, seed.py, prometheus.yml, setup_dev.sh
└── docker-compose.yml
```

## Default Credentials

| User | Password | Role |
|---|---|---|
| admin | Admin@1234 | Superadmin |
| operator1 | Operator@1234 | Operator |

**Change all passwords before any deployment.**

## Environment Variables

Copy `.env.example` → `.env` and set all values marked `change-me-*`.

## Model Setup

Place model weights in the `models/` directory:

```
models/
├── yolo/yolov8n.pt          # YOLOv8 nano (download from ultralytics)
├── face/buffalo_l/          # InsightFace buffalo_l model pack
└── anpr/anpr_yolo.pt        # ANPR-specific YOLO (optional — uses main YOLO if absent)
```

Download YOLOv8: `python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"`
InsightFace downloads automatically on first run.

## API Documentation

Set `APP_DEBUG=true` in `.env`, then visit:
- REST API: `https://localhost/docs`
- ReDoc: `https://localhost/redoc`
- AI Service: `http://localhost:8001/docs`

## License

Restricted — Government of India, SIH 2026. For evaluation purposes only.
