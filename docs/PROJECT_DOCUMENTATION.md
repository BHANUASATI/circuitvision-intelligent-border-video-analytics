# IBVAP — Intelligent Border Video Analytics Platform
## Complete Project Documentation
### Smart India Hackathon 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [Tech Stack — Full Summary](#3-tech-stack--full-summary)
4. [AI / Computer Vision Layer](#4-ai--computer-vision-layer)
   - 4.1 YOLO Object Detection
   - 4.2 ByteTrack Multi-Object Tracking
   - 4.3 Face Recognition Engine
   - 4.4 ANPR (Automatic Number Plate Recognition)
   - 4.5 Virtual Fence / Intrusion Detection
   - 4.6 Suspicious Activity Detection
   - 4.7 AI Pipeline Flow
5. [Backend Service](#5-backend-service)
   - 5.1 Framework & Core
   - 5.2 Database
   - 5.3 Authentication & Security
   - 5.4 Real-time: WebSocket + Redis
   - 5.5 HLS Video Streaming
   - 5.6 Monitoring
   - 5.7 API Endpoints
6. [AI Microservice](#6-ai-microservice)
7. [Frontend (React Dashboard)](#7-frontend-react-dashboard)
   - 7.1 Core Libraries
   - 7.2 UI & Styling
   - 7.3 Animations & Effects
   - 7.4 Charts & Data Visualization
   - 7.5 Live Video Playback
   - 7.6 Maps
   - 7.7 State Management
   - 7.8 Pages & Components
8. [Infrastructure & DevOps](#8-infrastructure--devops)
9. [Data Models](#9-data-models)
10. [Security Features](#10-security-features)
11. [Evidence Management](#11-evidence-management)
12. [Key Features Summary](#12-key-features-summary)
13. [How It All Works — End to End](#13-how-it-all-works--end-to-end)

---

## 1. Project Overview

**IBVAP (Intelligent Border Video Analytics Platform)** is an AI-powered, real-time border surveillance system built for the Smart India Hackathon 2026.

The platform ingests live RTSP/ONVIF camera feeds from border outposts (BOPs), runs a multi-stage AI pipeline on every frame, detects threats and suspicious activities, and pushes real-time alerts to a web-based command & control dashboard used by security personnel.

**Core Problem Solved:** Traditional border surveillance requires human operators to watch dozens of camera feeds simultaneously — leading to fatigue and missed threats. IBVAP automates detection, classification, and alerting so operators only need to act on confirmed events.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    NGINX (Reverse Proxy)                 │
│                    Port 80 / 443                         │
└─────┬────────────────────────┬───────────────────────────┘
      │                        │
      ▼                        ▼
┌──────────────┐      ┌─────────────────┐
│  React       │      │  FastAPI        │
│  Frontend    │◄────►│  Backend        │
│  (Vite SPA)  │      │  Port 8000      │
└──────────────┘      └────────┬────────┘
                               │
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
             ┌──────────┐ ┌────────┐ ┌──────────────┐
             │PostgreSQL│ │ Redis  │ │  AI Service  │
             │  (DB)    │ │(Cache/ │ │  Port 8001   │
             └──────────┘ │Pub-Sub)│ └──────┬───────┘
                          └────────┘        │
                                    ┌───────┴────────┐
                                    │   RTSP Cameras │
                                    │  (Border BOPs) │
                                    └────────────────┘
```

The system follows a **microservices architecture** with 4 core services:

| Service | Role | Port |
|---------|------|------|
| Frontend | React SPA dashboard | 80 (via Nginx) |
| Backend | FastAPI REST + WebSocket API | 8000 |
| AI Service | Computer vision & ML inference | 8001 |
| Nginx | Reverse proxy, SSL termination | 80/443 |

Supporting services: PostgreSQL 16, Redis 7, Prometheus, Grafana.

---

## 3. Tech Stack — Full Summary

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| React | 18.3.1 | UI framework |
| TypeScript | 5.4.5 | Type-safe JavaScript |
| Vite | 5.2.13 | Build tool & dev server |
| Tailwind CSS | 3.4.4 | Utility-first CSS framework |
| Redux Toolkit | 2.2.5 | Global state management |
| React Router DOM | 6.23.1 | Client-side routing |
| Recharts | 2.12.7 | Data visualization charts |
| hls.js | 1.5.15 | HLS video player |
| Leaflet + React-Leaflet | 1.9.4 | Interactive maps |
| Lucide React | 0.395.0 | Icon library |
| Axios | 1.7.2 | HTTP client |
| date-fns | 3.6.0 | Date formatting |
| clsx | 2.1.1 | Conditional CSS classes |
| tailwind-merge | 2.3.0 | Merge Tailwind classes |

### Backend
| Technology | Version | Purpose |
|---|---|---|
| FastAPI | 0.111.0 | REST API framework |
| Uvicorn | 0.29.0 | ASGI server |
| SQLAlchemy (async) | 2.0.30 | ORM |
| PostgreSQL | 16 | Primary database |
| Alembic | 1.13.1 | Database migrations |
| asyncpg | 0.29.0 | Async PostgreSQL driver |
| Redis | 5.0.4 | Pub/Sub + caching |
| python-jose | 3.3.0 | JWT tokens |
| passlib + bcrypt | 1.7.4 | Password hashing |
| slowapi | 0.1.9 | Rate limiting |
| Prometheus | — | Metrics collection |
| Loguru | 0.7.2 | Structured logging |

### AI / Computer Vision Service
| Technology | Version | Purpose |
|---|---|---|
| FastAPI | 0.111.0 | AI service API |
| Ultralytics (YOLOv8) | 8.2.18 | Object detection |
| OpenCV | 4.9.0.80 | Image processing |
| InsightFace (buffalo_l) | 0.7.3 | Face recognition |
| EasyOCR | 1.7.1 | License plate OCR |
| NumPy | 1.26.4 | Numerical computing |
| SciPy | 1.13.0 | Hungarian algorithm (tracking) |
| Shapely | 2.0.4 | Virtual fence geometry |
| scikit-learn | 1.4.2 | ML utilities |
| PyAV (av) | 12.0.0 | RTSP stream ingestion |
| ONVIF-Zeep | 0.2.12 | IP camera discovery |
| ONNX Runtime GPU | 1.17.3 | GPU inference |
| Redis | 5.0.4 | Alert pub/sub |
| Loguru | 0.7.2 | Logging |

### Infrastructure
| Technology | Purpose |
|---|---|
| Docker + Docker Compose | Containerization |
| Nginx 1.25 | Reverse proxy + SSL |
| Prometheus 2.51.2 | Metrics collection |
| Grafana 10.4.2 | Metrics visualization |
| NVIDIA GPU (CUDA) | GPU acceleration for AI |
| FFmpeg | RTSP → HLS transcoding |

---

## 4. AI / Computer Vision Layer

The AI layer is the heart of IBVAP. Every camera runs its own `StreamWorker` — an async task that ingests RTSP frames and passes them through a 6-stage AI pipeline.

### 4.1 YOLO Object Detection

**Model:** `YOLOv8n` (nano variant — fast, GPU-optimized)
**Library:** `ultralytics==8.2.18`
**File:** `ai_service/modules/detection/detector.py`

**What it detects:**
| COCO Class ID | Label |
|---|---|
| 0 | person |
| 1 | bicycle |
| 2 | car |
| 3 | motorcycle |
| 5 | bus |
| 7 | truck |

**Configuration:**
- Confidence threshold: `0.45` (45% minimum confidence)
- NMS (Non-Maximum Suppression) IoU threshold: `0.45`
- Device: GPU (CUDA device 0) by default, falls back to CPU
- Model path: `/models/yolo/yolov8n.pt`

**How it works:**
1. The YOLO model is lazy-loaded on first use (thread-safe via a lock)
2. For each frame, `model.predict()` runs inference
3. Results are filtered to only the classes we care about (persons, vehicles)
4. Bounding boxes in `xyxy` format are returned with class ID, label, and confidence

**Second YOLO model for ANPR:**
- A separate fine-tuned YOLO model (`/models/anpr/anpr_yolo.pt`) is used specifically for license plate localization
- This is a specialized model trained to detect rectangular plate regions

### 4.2 ByteTrack Multi-Object Tracking

**Algorithm:** ByteTrack (published paper: arxiv.org/abs/2110.06864)
**File:** `ai_service/modules/tracking/bytetrack.py`
**Implementation:** Custom pure-Python implementation (no external package)

ByteTrack assigns persistent IDs to detected objects across frames — so even if a person disappears momentarily (occlusion), they regain the same ID when they reappear.

**How it works:**

1. **Kalman Filter** predicts the next position of each tracked object using constant-velocity motion model (state: `[cx, cy, w, h, vx, vy, vw, vh]`)
2. **Dual threshold matching:** detections split into high-confidence (≥0.45) and low-confidence (0.1–0.45) sets
3. **Hungarian Algorithm** (`scipy.optimize.linear_sum_assignment`) matches detected boxes to existing tracks using IoU (Intersection over Union) cost
4. **Two-round matching:**
   - Round 1: High-confidence detections matched to active tracks
   - Round 2: Low-confidence detections matched to unmatched tracks (rescues partial occlusions)
   - Round 3: Unmatched high-confidence detections try to match lost tracks
5. **Track lifecycle:** NEW → TRACKED → LOST → REMOVED (track kept for 30 frames after disappearing)

**Key parameters:**
- `high_thresh = 0.5` — confidence above this = high-quality detection
- `min_hits = 3` — track confirmed only after seen 3 consecutive times
- `max_lost_frames = 30` — track removed after 30 frames without update

### 4.3 Face Recognition Engine

**Model:** InsightFace `buffalo_l`
**Library:** `insightface==0.7.3`, `onnxruntime-gpu==1.17.3`
**File:** `ai_service/modules/face_recognition/face_engine.py`

The `buffalo_l` model is InsightFace's large detection + recognition bundle:
- **Face Detector:** RetinaFace (detects face bounding boxes + 5-point landmarks)
- **Feature Extractor:** ArcFace (generates 512-dimensional face embedding)

**Pipeline:**
1. `app.get(frame)` — detects all faces in a frame
2. For each face, extracts a 512-D embedding vector
3. Embedding compared against an enrolled face database using **cosine similarity**
4. If cosine similarity ≥ 0.5 threshold → identity match
5. Checks if matched identity is in the **watchlist**
6. Unknown faces (no match) also generate alerts

**Face Database storage:**
```
/data/face_db/
  embeddings/<identity_id>.npy   ← 512-D numpy array
  metadata/<identity_id>.json    ← name, category, enrolled_at
  watchlist.json                 ← list of watchlisted identity IDs
```

**Cosine similarity batch computation:**
The system uses vectorized NumPy matrix multiplication to compare one query embedding against all enrolled embeddings simultaneously — very fast even with thousands of enrollments.

**Sampling:** Face recognition runs every 5th processed frame (not every frame) to reduce GPU load.

### 4.4 ANPR (Automatic Number Plate Recognition)

**Library:** `easyocr==1.7.1` + YOLO plate detector
**File:** `ai_service/modules/anpr/anpr.py`

**Pipeline:**
1. YOLO plate detection model localizes plate bounding boxes
2. Crop the plate region from the frame (with 10px padding)
3. Preprocessing: resize to standard height (64px), grayscale → adaptive threshold → denoise
4. EasyOCR reads the plate text (only `A-Z 0-9 -` characters allowed)
5. Clean plate text: uppercase, strip non-alphanumeric except hyphens
6. Fuzzy match against watchlist file (`plate_db/watchlist.txt`)

**OCR configuration:**
- Language: English only
- GPU enabled when CUDA is available
- Minimum confidence: 0.3 (below this, result discarded)
- Minimum plate length: 4 characters

**Sampling:** ANPR runs every 3rd processed frame and only when vehicle tracks are present.

### 4.5 Virtual Fence / Intrusion Detection

**Library:** `Shapely==2.0.4` (geometric calculations)
**File:** `ai_service/modules/intrusion/virtual_fence.py`

Two types of virtual fences:

**1. Line Crossing Detection:**
- Draw a virtual line on the camera view
- The system tracks which side of the line each object is on
- When an object crosses from one side to the other, an intrusion event fires
- Supports directional detection (A→B only, B→A only, or both)
- Cross-product math: `(x2-x1)*(y-y1) - (y2-y1)*(x-x1)` determines point side (+1 or -1)

**2. Polygon Zone Intrusion:**
- Define a polygonal restricted zone (minimum 3 points)
- Uses `shapely.geometry.Polygon.contains(Point(center))` to test if an object's center is inside the zone
- Alert fired when any tracked object enters the zone

**Alert cooldown:** 30 seconds per (fence, track) pair — prevents alert flooding.

### 4.6 Suspicious Activity Detection

**File:** `ai_service/modules/activity/activity_detector.py`

Maintains a **trajectory history** for every tracked person across frames. Detects 6 activity types:

| Activity | Detection Method | Severity |
|---|---|---|
| **Loitering** | Person in area >30s with speed <5px/s | MEDIUM |
| **Crowding** | ≥5 persons detected simultaneously | HIGH |
| **Running** | Average speed >80px/s over last 5 positions | MEDIUM |
| **Night Movement** | Frame brightness (mean gray value) <50 + any person present | HIGH |
| **Erratic Movement** | Mean trajectory direction change angle >120° | MEDIUM |
| **Abandoned Object** | Non-person detection stationary >60s | (configurable) |

**Speed calculation:** Euclidean distance between consecutive trajectory positions, normalized by FPS.

**Night detection:** `cv2.cvtColor(frame, BGR2GRAY)` then `np.mean(gray) < 50.0`

### 4.7 AI Pipeline Flow

For every camera frame (after frame-skip):

```
Frame Input (BGR numpy array)
        │
        ▼
1. YOLO Detection ─────────────────────────────────► Bounding boxes + class labels
        │
        ▼
2. ByteTrack ──────────────────────────────────────► Persistent track IDs assigned
        │
        ├──────────────────────────────────────────► 3. Virtual Fence Check
        │                                               (Shapely line/polygon math)
        ├──────────────────────────────────────────► 4. Activity Analysis
        │                                               (Trajectory + heuristics)
        ├── every 5th frame ──────────────────────► 5. Face Recognition
        │                                               (InsightFace buffalo_l)
        └── every 3rd frame + vehicles present ──► 6. ANPR
                                                       (YOLO plate + EasyOCR)
        │
        ▼
Alerts assembled → Published to Redis channel "ibvap:alerts"
        │
        ▼
Backend Redis subscriber → WebSocket → Frontend dashboard
```

---

## 5. Backend Service

**Framework:** FastAPI 0.111.0
**Server:** Uvicorn with uvloop (high-performance async event loop)
**File:** `backend/app/main.py`

### 5.1 Framework & Core

FastAPI was chosen because:
- Native `async/await` support matches the event-driven nature of surveillance (WebSockets, streaming)
- Auto-generated OpenAPI (`/docs`) for rapid API testing
- Pydantic v2 for data validation
- Dependency injection for clean auth/DB access

### 5.2 Database

**PostgreSQL 16** with full async access:
- `SQLAlchemy 2.0` asyncio mode — no blocking DB calls
- `asyncpg` — fastest async PostgreSQL driver for Python
- `Alembic` — version-controlled schema migrations

**Tables:**
- `users` — operator accounts (RBAC roles: admin, operator, viewer)
- `cameras` — registered camera devices
- `alerts` — AI-generated security alerts
- `incidents` — grouped alert collections (security incidents)
- `incident_alerts` — junction table (many-to-many: incidents ↔ alerts)
- `audit_logs` — every user action logged for accountability

### 5.3 Authentication & Security

**JWT tokens** (JSON Web Tokens):
- Access token: short-lived (default 15 minutes)
- Refresh token: longer-lived for session renewal
- Library: `python-jose[cryptography]` — RS256/HS256 signing
- Password hashing: `passlib + bcrypt` (industry-standard one-way hash)

**RBAC (Role-Based Access Control):**
- Roles: `admin`, `operator`, `viewer`
- Protected routes use `Depends(get_current_user)` FastAPI dependency
- Audit trail: every login, logout, action logged to `audit_logs` table

**Rate Limiting:** `slowapi` limits API calls per IP to prevent brute-force attacks.

### 5.4 Real-time: WebSocket + Redis

**How real-time alerts reach the dashboard:**

```
AI Service
    │
    └─► Redis PUBLISH("ibvap:alerts", alert_json)
               │
        Backend Redis Subscriber (asyncio task)
               │
               └─► WebSocket Manager broadcasts to all connected clients
                          │
                   Frontend WebSocket client
                          │
                   Redux: pushLiveAlert() action
                          │
                   Alert feed updates in real-time
```

The WebSocket endpoint (`/api/v1/ws/alerts`) authenticates via JWT as a query parameter:
```
ws://server/api/v1/ws/alerts?token=<JWT>&camera_id=cam-01
```

Clients can filter alerts to specific cameras using the `camera_id` query param or by sending `{"action": "subscribe", "camera_id": "cam-01"}` after connecting.

A keepalive ping/pong mechanism runs every configurable interval to maintain connections.

### 5.5 HLS Video Streaming

**RTSP → HLS conversion using FFmpeg:**

When the user clicks "View" on a camera, the backend:
1. Validates the camera exists and the stream URL is configured
2. Does a TCP pre-flight check: tries to connect to the camera host:port before spawning FFmpeg
3. Launches FFmpeg as a subprocess: `ffmpeg -i rtsp://... -hls_time 2 -hls_list_size 5 index.m3u8`
4. Polls for the first `.m3u8` playlist file to appear (up to 15 seconds)
5. Returns the playlist URL to the frontend

The frontend's **hls.js** player then fetches segments directly from the backend serving `.ts` files.

**HLS configuration (low-latency):**
- `liveSyncDurationCount: 2` — sync to 2 segments behind live edge
- `liveMaxLatencyDurationCount: 5` — max 5 segments behind live edge
- `maxBufferLength: 10` — buffer up to 10 seconds

### 5.6 Monitoring

**Prometheus** scrapes metrics from the backend's `/metrics` endpoint (via `prometheus-fastapi-instrumentator`):
- Request count, latency, status codes per endpoint
- Active WebSocket connections
- Database query times

**Grafana** connects to Prometheus to build dashboards for system health monitoring — separate from the operator dashboard.

### 5.7 API Endpoints

All under `/api/v1/`:

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/login` | JWT login |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Current user info |
| GET | `/cameras` | List all cameras |
| POST | `/cameras` | Add a new camera |
| DELETE | `/cameras/{id}` | Remove camera |
| POST | `/stream/{camera_id}/start` | Start HLS stream |
| POST | `/stream/{camera_id}/stop` | Stop HLS stream |
| GET | `/stream/{camera_id}/hls/index.m3u8` | Serve HLS playlist |
| GET | `/alerts` | List alerts (filterable) |
| PATCH | `/alerts/{id}` | Acknowledge/resolve alert |
| GET | `/analytics/dashboard` | Dashboard summary stats |
| GET | `/analytics/timeline` | Event type over time |
| GET | `/analytics/heatmap` | Alert volume by camera |
| GET | `/incidents` | List incidents |
| POST | `/incidents` | Create incident |
| WS | `/ws/alerts` | Real-time alert WebSocket |

---

## 6. AI Microservice

**File:** `ai_service/main.py`

A standalone FastAPI app running on port 8001, separate from the backend. This separation ensures:
- GPU-heavy AI work doesn't block REST API responses
- Can be scaled independently (e.g., multiple GPU nodes)
- Single worker mode — GPU is not fork-safe

**Stream Manager:** `ai_service/core/stream_manager.py`
- Singleton that manages all `StreamWorker` instances
- Creates one `asyncio.Task` per camera
- Thread/task-safe via `asyncio.Lock()`
- Supports up to 16 concurrent streams by default

**Stream Worker:** `ai_service/core/stream_worker.py`
- One worker per camera running as an async task
- CPU/IO work (frame reading) done in `asyncio.run_in_executor()` to avoid blocking the event loop
- AI inference pipeline runs in thread pool workers
- Exponential backoff reconnection (5s → 10s → 20s ... max 60s)
- Real-time FPS tracking (calculated every 30 frames)
- Statistics exposed: `fps`, `frame_count`, `inference_ms`, `alert_count`

---

## 7. Frontend (React Dashboard)

**File structure:**
```
frontend/src/
  App.tsx              ← Route configuration
  main.tsx             ← React DOM entry point
  index.css            ← Global Tailwind + custom CSS
  pages/               ← One file per page
  components/          ← Reusable UI components
    common/            ← Layout, Sidebar, TopBar, Toast, etc.
    dashboard/         ← StatCard, AlertTrendChart, EventTypeChart
    cameras/           ← CameraCard, CameraViewer
    alerts/            ← AlertFeed
    analytics/         ← Analytics charts
  store/               ← Redux Toolkit state
    slices/            ← authSlice, alertsSlice, camerasSlice, uiSlice
  api/                 ← Axios API client + typed endpoints
  hooks/               ← Custom React hooks
  types/               ← TypeScript interfaces
  utils/               ← Utility functions
```

### 7.1 Core Libraries

**React 18.3.1**
- Uses Concurrent Mode features
- Component-based architecture
- Hooks: `useState`, `useEffect`, `useRef`, `useCallback`, `useEffect`

**TypeScript 5.4.5**
- Full type safety across the codebase
- Typed API responses, Redux state, component props
- `tsconfig.json` with strict mode enabled

**React Router DOM 6.23.1**
- Client-side routing with `BrowserRouter`
- Protected routes via `RequireAuth` wrapper component
- `Navigate` for redirects
- `NavLink` for active route highlighting in sidebar

### 7.2 UI & Styling

**Tailwind CSS 3.4.4** with custom theme in `tailwind.config.js`:

**Custom Color Palette:**
```js
brand:    { 500: "#0ea5e9", 600: "#0284c7" }   // Sky blue — primary actions
surface:  { DEFAULT: "#0f172a",                 // Dark navy background
            card:    "#1e293b",                 // Slightly lighter cards
            border:  "#334155" }                // Subtle borders
severity: { low: "#22c55e", medium: "#f59e0b",  // Green/amber/red/darkred
            high: "#ef4444", critical: "#dc2626" }
```

**Custom Fonts:**
- `Inter` — sans-serif for UI text (modern, clean)
- `JetBrains Mono` — monospace for camera IDs, timestamps, technical values

**Custom CSS Component Classes** (in `index.css`):
- `.card` — glassmorphism-style dark card with border
- `.btn-primary` — sky blue filled button with hover + focus ring
- `.btn-ghost` — transparent button with hover background
- `.badge` — small pill-shaped tag
- `.input` — dark-themed input with brand focus ring
- `.severity-*` — colored severity badges (low/medium/high/critical)
- `.status-*` — colored status badges (new/acknowledged/resolved)

**PostCSS + Autoprefixer** for CSS browser compatibility.

**clsx + tailwind-merge:**
- `clsx` — conditionally joins class names: `clsx("btn", isActive && "bg-blue-600")`
- `tailwind-merge` — merges Tailwind classes without conflicts

**Lucide React 0.395.0** — icon library with 400+ clean SVG icons. Used throughout:
- `Shield` — brand logo
- `Camera`, `Bell`, `AlertTriangle`, `BarChart3`, `Users` — sidebar navigation
- `RefreshCw`, `Search`, `Plus`, `Filter` — action buttons
- `Loader2` — loading spinner with spin animation
- `Eye`, `EyeOff` — password visibility toggle
- `X`, `Maximize2`, `Minimize2`, `Volume2`, `VolumeX` — video player controls
- `CheckCheck` — resolve alert button

### 7.3 Animations & Effects

All animations are defined in `tailwind.config.js` and `index.css`:

**1. `animate-fade-in`**
```css
fadeIn: { "0%": { opacity: 0 }, "100%": { opacity: 1 } }
/* Duration: 0.3s ease-out */
```
Used on: every page wrapper (`<div className="space-y-6 animate-fade-in">`). Every time you navigate to a new page, it smoothly fades in.

**2. `animate-slide-in`**
```css
slideIn: { "0%": { transform: "translateX(100%)" }, "100%": { transform: "translateX(0)" } }
/* Duration: 0.2s ease-out */
```
Used on: toast notifications sliding in from the right.

**3. `animate-pulse-alert`**
```css
"pulse 1.5s cubic-bezier(0.4,0,0.6,1) infinite"
```
Used on: CRITICAL severity badges — they pulse red to grab operator attention. Also used on the unread alert count badge in the TopBar.

**4. `animate-spin`**
Used on: `Loader2` icon (login button while authenticating, Refresh button while loading data).

**5. `animate-ping`**
```html
<span className="animate-ping absolute ... bg-red-400 opacity-75" />
<span className="relative ... bg-red-500" />
```
Used on: the **LIVE indicator dot** on the CameraViewer — a red pulsing ring around a solid red dot, resembling a live recording indicator.

**6. Sidebar collapse transition**
```css
transition-all duration-200
w-56 (expanded) ↔ w-14 (collapsed)
```
The sidebar smoothly narrows from 224px to 56px when the collapse button is clicked.

**7. Sidebar icon rotation**
```css
<ChevronLeft className={clsx("transition-transform", !open && "rotate-180")} />
```
The chevron icon rotates 180° when the sidebar collapses — smooth CSS transform transition.

**8. NavLink active state**
Active navigation items get `bg-brand-600/20 text-brand-400` — a subtle highlight with the brand color.

**9. Table row hover**
```css
hover:bg-surface/50 transition-colors
```
Alert table rows get a subtle background on hover.

**10. Button hover transitions**
All buttons use `transition-colors` — color changes animate smoothly rather than snapping.

**11. Recharts SVG gradient (Area chart)**
```jsx
<linearGradient id="alertGrad" x1="0" y1="0" x2="0" y2="1">
  <stop offset="5%"  stopColor="#0ea5e9" stopOpacity={0.3} />
  <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
</linearGradient>
```
The alert trend area chart fills with a gradient that fades from sky blue to transparent — a modern "glow" chart effect.

**12. Login page background grid**
```jsx
<div style={{
  backgroundImage: "linear-gradient(rgba(14,165,233,.5) 1px,transparent 1px), ...",
  backgroundSize: "40px 40px",
}} />
```
A subtle grid pattern behind the login form, matching a cybersecurity/tech aesthetic.

**13. System status pulse dot**
```html
<span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
```
Shown at the bottom of the sidebar — "System Operational" with a pulsing green dot.

**14. Video player backdrop blur**
```css
bg-black/80 backdrop-blur-sm
```
The CameraViewer modal uses `backdrop-filter: blur()` on the overlay behind the video.

### 7.4 Charts & Data Visualization

**Library: Recharts 2.12.7**

All charts use `<ResponsiveContainer>` to auto-scale to their parent container.

**Alert Trend Chart** (`AlertTrendChart.tsx`):
- Type: `AreaChart`
- Shows alerts over the last 24 hours (hourly)
- SVG gradient fill below the line
- Dark themed: `#1e293b` tooltip background, `#334155` grid lines

**Event Type Chart** (`EventTypeChart.tsx`):
- Type: `PieChart` or `BarChart` (event type distribution)

**Analytics — Event Types Over Time** (`AnalyticsPage.tsx`):
- Type: `LineChart` with multiple lines
- Each event type (face_alert, intrusion, anpr, etc.) is a separate colored line
- 8-color palette: `["#0ea5e9","#8b5cf6","#f59e0b","#ef4444","#22c55e","#ec4899","#06b6d4","#f97316"]`
- `dot={false}` for clean continuous lines

**Analytics — Camera Heatmap** (`AnalyticsPage.tsx`):
- Type: `BarChart` with horizontal layout (`layout="vertical"`)
- Shows total alert volume per camera
- Each bar gets a different color from the 8-color palette via `<Cell>`

**Date Formatting:** `date-fns 3.6.0`
- `format(parseISO(hour), "HH:mm")` — formats ISO timestamps to hour:minute for chart X-axis
- `formatDistanceToNow(date, { addSuffix: true })` — "2 minutes ago", "1 hour ago" in the alerts table
- `format(new Date(), "EEEE, dd MMM yyyy • HH:mm")` — full date in TopBar

### 7.5 Live Video Playback

**Library: hls.js 1.5.15**
**File:** `frontend/src/components/cameras/CameraViewer.tsx`

**Flow:**
1. User clicks a camera card → `CameraViewer` modal opens
2. Frontend POSTs to `/api/v1/stream/{camera_id}/start`
3. Backend spawns FFmpeg: `RTSP → HLS (.m3u8 + .ts segments)`
4. Backend returns `playlist_url`
5. `hls.js` loads the playlist and attaches to `<video>` element
6. Video plays with low latency HLS configuration
7. On modal close → POST `/api/v1/stream/{camera_id}/stop` (kills FFmpeg)

**Browser compatibility:**
- Chrome/Firefox/Edge: `hls.js` handles everything
- Safari/iOS: native HLS support via `video.canPlayType("application/vnd.apple.mpegurl")`

**Features shown in the video player:**
- Live indicator (pulsing red dot)
- Camera name, ID, location
- Mute/unmute toggle
- Fullscreen toggle (native browser Fullscreen API)
- Escape key closes the modal
- Loading overlay while stream starts
- Error overlay with retry button if stream fails
- Bottom status bar showing `RTSP → HLS` and current phase (STARTING / PLAYING / ERROR)

### 7.6 Maps

**Library: Leaflet 1.9.4 + React-Leaflet 4.2.1**

Used for geographic camera placement visualization. Leaflet is a lightweight open-source mapping library.

**Dark mode overrides** (in `index.css`):
```css
.leaflet-container { background: #0f172a !important; }
.leaflet-tile { filter: brightness(0.6) saturate(0.8) !important; }
```
Map tiles are darkened and desaturated to match the dark surveillance dashboard theme.

### 7.7 State Management

**Redux Toolkit 2.2.5**
**File:** `frontend/src/store/`

Four Redux slices:

**`authSlice`** — Authentication state:
- `token`, `user`, `loading`, `error`
- Async thunks: `login`, `verifyAuth`
- Token persisted in `localStorage`

**`alertsSlice`** — Alert management:
- `items` (paginated alerts), `counts` (severity counts), `liveAlerts` (real-time, capped at 100)
- Async thunks: `fetchAlerts`, `fetchCounts`, `ackAlert`
- Reducer: `pushLiveAlert` (called when WebSocket pushes new alert)

**`camerasSlice`** — Camera registry:
- `items`, `loading`
- Async thunk: `fetchCameras`

**`uiSlice`** — UI state:
- `sidebarOpen`, `alertPanelOpen`
- Reducers: `toggleSidebar`, `toggleAlertPanel`, `addToast`, `removeToast`

**Real-time alert flow in Redux:**
WebSocket message → `pushLiveAlert(alert)` action → `state.liveAlerts.unshift(payload)` + also prepended to `state.items`

### 7.8 Pages & Components

**Pages:**

| Page | Route | What it shows |
|---|---|---|
| `LoginPage` | `/login` | Secure login form with JWT auth |
| `DashboardPage` | `/dashboard` | KPI cards, alert trend chart, severity breakdown |
| `CamerasPage` | `/cameras` | Camera grid with search, add camera form, live viewer |
| `AlertsPage` | `/alerts` | Filterable alert table with acknowledge/resolve/false-positive actions |
| `IncidentsPage` | `/incidents` | Security incidents (grouped alerts) |
| `AnalyticsPage` | `/analytics` | Multi-line event type chart + camera heatmap |
| `UsersPage` | `/users` | Operator user management (admin only) |

**Key Components:**

- `Layout` — main app shell: Sidebar + TopBar + `<Outlet>` (React Router)
- `Sidebar` — collapsible navigation with alert count badge and active route highlighting
- `TopBar` — live clock, alert notification bell with unread count, user menu, logout
- `StatCard` — KPI metric card with icon, value, subtitle, and color-coded icon background
- `CameraCard` — camera grid tile showing name, location, streaming status
- `CameraViewer` — full-screen modal HLS video player
- `AlertFeed` — real-time alert sidebar panel
- `SeverityBadge` — colored pill badge (LOW/MEDIUM/HIGH/CRITICAL)
- `ToastContainer` — slide-in toast notifications (slide-in animation)
- `LoadingSpinner` — centered spinner, supports `fullScreen` prop

---

## 8. Infrastructure & DevOps

**Docker Compose** orchestrates all 8 services:

```
Services:
  postgres     ← PostgreSQL 16 Alpine
  redis        ← Redis 7 Alpine (password protected, 512MB max, LRU eviction)
  ai_service   ← Python + GPU (CUDA), OpenCV, YOLO, InsightFace
  backend      ← Python FastAPI, PostgreSQL, Redis
  frontend     ← React build, served by Nginx SPA config
  nginx        ← Reverse proxy, SSL, routes /api → backend, / → frontend
  prometheus   ← Metrics collection (30 days retention)
  grafana      ← Metrics dashboards
```

**GPU support in Docker:**
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [gpu]
```
Requires NVIDIA Container Toolkit installed on the host.

**Health checks:** All critical services have Docker health checks so dependent services wait for them to be ready (using `depends_on: condition: service_healthy`).

**Logging:** JSON file logging driver with 50MB max size, 5 file rotation.

**Volumes (persistent data):**
- `postgres_data` — database files
- `redis_data` — Redis persistence
- `evidence_data` — saved frame evidence (JPEG + SHA-256 sidecars)
- `models_data` — YOLO + InsightFace model weights
- `face_db_data` — enrolled face embeddings
- `plate_db_data` — ANPR watchlist
- `prometheus_data` / `grafana_data` — monitoring data

**Nginx:**
- Reverse proxies `/api/v1/` → backend:8000
- Reverse proxies `/ws/` → backend:8000 (WebSocket upgrade headers)
- Serves frontend SPA with `try_files $uri $uri/ /index.html` (handles client-side routing)
- SSL termination at port 443

---

## 9. Data Models

### Alert
```
id              UUID (primary key)
alert_id        String (unique, indexed) — from AI service
camera_id       String (FK → cameras)
event_type      String — "intrusion"|"face_alert"|"anpr"|"loitering"|"crowding"|...
severity        String — "LOW"|"MEDIUM"|"HIGH"|"CRITICAL"
status          String — "new"|"acknowledged"|"resolved"|"false_positive"
description     Text
payload         JSON text — bbox, confidence, track_id, etc.
evidence_path   Text — path to saved JPEG
evidence_hash   String (64) — SHA-256 hash for tamper detection
acknowledged_by UUID (FK → users)
acknowledged_at DateTime
created_at      DateTime (indexed)
```

### Camera
- camera_id, name, stream_url, location, is_streaming
- Feature flags: enable_detection, enable_face_recognition, enable_anpr, enable_intrusion, enable_activity
- frame_skip (performance tuning)

### User
- id, username, email, hashed_password (bcrypt)
- role: admin | operator | viewer
- is_active, created_at

### Incident
- Groups multiple alerts into one security incident
- title, description, severity, status (open/in_progress/resolved/closed)
- assigned_to (operator)
- resolved_at timestamp

---

## 10. Security Features

1. **JWT Authentication** — stateless, short-lived access tokens + refresh tokens
2. **bcrypt Password Hashing** — industry-standard, computationally expensive hash
3. **RBAC** — admin/operator/viewer roles with route-level protection
4. **Rate Limiting** — `slowapi` prevents brute-force login attacks
5. **CORS** — configurable allowed origins list
6. **WebSocket Auth** — JWT validated before WebSocket connection accepted (closes with 4001 if invalid)
7. **Audit Logging** — every user action, login, and status change logged
8. **Evidence Integrity** — SHA-256 hash saved alongside every evidence JPEG; `verify_evidence()` method detects tampering
9. **Alert Cooldown** — 30-second cooldown per (camera, fence, track) prevents alert flooding
10. **DB Isolation** — AI service and backend run as separate containers; DB not exposed externally

---

## 11. Evidence Management

**File:** `ai_service/utils/evidence.py`

When an alert fires (intrusion, face alert, ANPR watchlist hit), the system:
1. Saves the frame as a high-quality JPEG (95% quality)
2. Computes a **SHA-256 hash** of the JPEG file
3. Writes a **sidecar JSON** file alongside the image:
```json
{
  "evidence_id": "uuid-...",
  "camera_id": "cam-bop-01",
  "event_type": "intrusion",
  "timestamp": "2026-09-02T14:30:00Z",
  "filename": "uuid-....jpg",
  "sha256": "a3f4c2...",
  "metadata": { "fence_id": "fence-north-01", "track_id": 42 }
}
```

Evidence is organized by directory:
```
/data/evidence/
  {camera_id}/
    {event_type}/
      {YYYY}/{MM}/{DD}/{HH}/
        {evidence_id}.jpg
        {evidence_id}.json
```

The hash can be verified later to prove the image has not been tampered with — important for legal/forensic use.

---

## 12. Key Features Summary

| Feature | Technology Used |
|---|---|
| Object Detection | YOLOv8 (Ultralytics) |
| ANPR Plate Detection | YOLO fine-tuned on license plates |
| ANPR OCR | EasyOCR |
| Face Recognition | InsightFace buffalo_l (RetinaFace + ArcFace) |
| Multi-Object Tracking | ByteTrack (custom Python implementation) |
| Virtual Fences | Shapely (polygon/line geometry) |
| Activity Analysis | Custom trajectory heuristics |
| Stream Ingestion | OpenCV VideoCapture + PyAV |
| RTSP → Web Video | FFmpeg → HLS → hls.js |
| Real-time Alerts | Redis Pub/Sub → WebSocket → React |
| Data Storage | PostgreSQL 16 (async SQLAlchemy) |
| REST API | FastAPI |
| Frontend | React 18 + TypeScript + Vite |
| Styling | Tailwind CSS (dark theme) |
| Charts | Recharts |
| Maps | Leaflet |
| State | Redux Toolkit |
| Auth | JWT (access + refresh tokens) |
| Password Security | bcrypt |
| GPU Inference | CUDA via ONNX Runtime + PyTorch |
| Containerization | Docker Compose |
| Monitoring | Prometheus + Grafana |
| Evidence Integrity | SHA-256 hashing |

---

## 13. How It All Works — End to End

Here is the complete journey from a camera detecting an intruder to an operator acknowledging the alert:

**Step 1 — Operator logs in**
- Opens the React dashboard, enters credentials
- Frontend `authSlice` calls `POST /api/v1/auth/login`
- Backend verifies bcrypt hash, returns JWT access + refresh tokens
- Tokens stored in `localStorage`, user redirected to `/dashboard`

**Step 2 — Camera registered**
- Operator navigates to Cameras, clicks "Add Camera"
- Fills in camera ID, name, RTSP URL, location, enables desired AI modules
- `POST /api/v1/cameras` saves to PostgreSQL
- Backend calls AI Service to start a `StreamWorker` for this camera

**Step 3 — AI Stream Worker starts**
- `StreamManager` creates a new `StreamWorker` as an asyncio task
- Worker opens an OpenCV `VideoCapture` pointing at the RTSP URL
- Begins reading frames at up to 25 FPS, skipping every 2nd frame for efficiency

**Step 4 — AI Pipeline processes frames**
- For each processed frame, the 6-stage pipeline runs in a thread pool:
  1. YOLOv8 detects persons and vehicles
  2. ByteTrack assigns persistent IDs
  3. Shapely checks virtual fence crossings
  4. Activity detector checks for loitering, crowding, running, night movement
  5. InsightFace checks for watchlisted faces (every 5th frame)
  6. EasyOCR reads license plates (every 3rd frame if vehicles present)

**Step 5 — Alert generated**
- An intruder crosses the north fence virtual line
- `VirtualFenceManager.check_frame()` detects the crossing
- An alert dict is built: `{alert_id, event_type: "intrusion", camera_id, timestamp, data: {fence_name, track_id, bbox}}`
- The frame is saved as JPEG evidence with SHA-256 hash
- Alert is published to Redis: `PUBLISH ibvap:alerts {alert_json}`

**Step 6 — Alert reaches the dashboard**
- Backend's Redis subscriber (running as asyncio background task) receives the message
- `WebSocketManager.broadcast()` sends the alert JSON to all connected clients
- Frontend's WebSocket `onmessage` handler fires
- Redux `pushLiveAlert(alert)` action updates state
- Alert count badge in TopBar increments and pulses
- Alert appears in the real-time AlertFeed panel

**Step 7 — Operator acknowledges**
- Operator clicks "ACK" on the alert in the Alerts page
- `PATCH /api/v1/alerts/{id}` called with `status: "acknowledged"`
- Backend updates PostgreSQL, logs the action to audit_logs
- Alert status badge in the table changes from blue "new" to grey "acknowledged"

**Step 8 — Operator views the camera**
- Operator clicks "View" on the camera card
- CameraViewer modal opens, `POST /api/v1/stream/{camera_id}/start` called
- Backend TCP-pings the camera host, spawns FFmpeg converting RTSP → HLS
- hls.js loads the playlist, video plays in the browser
- Live red pulsing dot confirms the feed is live

---

*This documentation covers the complete IBVAP system as built for SIH 2026.*
*All AI inference, real-time streaming, alert management, and frontend UI components are production-ready implementations.*
