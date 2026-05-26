# Orbital Tracker

A real-time satellite tracking platform that fetches live orbital data from NASA's Celestrak, computes accurate positions using the SGP4 propagation algorithm, and visualizes satellites on a 3D globe.

**Live demo:** https://d3n8lb03lz0jyt.cloudfront.net

---

## What It Does

There are thousands of satellites constantly passing that we never see. This project makes that visible. You can watch the ISS move in real time, see which satellites are directly above your location right now, and detect when two satellites are on a collision course.

- Live position tracking for 10,000+ satellites across multiple groups (ISS complex, Starlink, weather satellites)
- 90-minute orbital path projection for any satellite
- Conjunction detection — identifies satellites whose orbital paths bring them dangerously close
- "Near me" query — returns satellites currently within a geographic radius of your location
- Featured satellites panel with curated iconic objects (ISS, Hubble, GOES-16)
- Position data auto-refreshes every 30 seconds; TLE data refreshes every 24 hours via a scheduled background job

---

## Architecture

```
Browser
   │
   ▼
AWS CloudFront (HTTPS)
   ├── /* ──────────────► AWS S3 (React frontend)
   └── /api/* ──────────► AWS EC2 (FastAPI backend)
                               │
                         ┌─────┴─────┐
                         ▼           ▼
                    PostgreSQL     Redis
                    (satellite     (position
                     TLE data)      cache)
```

The frontend and backend share a single CloudFront distribution. Routing `/api/*` requests through CloudFront to EC2 eliminates mixed content issues without requiring a custom domain or managing SSL certificates separately.

---

## How the Physics Works

Satellite positions aren't stored, they're computed on demand. Each satellite's orbital parameters are stored as a Two-Line Element set (TLE), which encodes inclination, eccentricity, altitude, and decay rate. On every position request, the SGP4 algorithm propagates the TLE forward to the current timestamp, returning a position in Earth-Centered Inertial (ECI) coordinates. Those coordinates are then converted to latitude, longitude, and altitude using standard geodetic transforms.

SGP4 is the same algorithm NASA and NORAD use operationally. TLEs go stale within days as orbits decay, which is why the scheduler refreshes them from Celestrak every 24 hours.

---

## Caching Strategy

Running SGP4 on 500 satellites per request is CPU-intensive. Without caching, every user hitting the position endpoint triggers the same computation. I added a Redis cache with the cache-aside pattern and time-bucketed keys:

```python
bucket = int(now.timestamp() // 10)
cache_key = f"positions:{group}:{limit}:{bucket}"
```

Bucketing time into 10-second windows means all requests within the same window share a single cached result. Measured improvement: **~80ms cold → ~1.4ms warm** (~50x speedup on cache hits).

This design means if Redis is unavailable, the app falls back to direct computation without crashing.

---

## Conjunction Detection

The conjunction detection algorithm checks every pair of satellites within a group for close approaches over a configurable time window. It uses Euclidean distance between ECI positions rather than geodetic distance, which is more accurate for objects in orbit.

One interesting edge case: satellites physically docked to the ISS (Crew Dragon, Cygnus, Soyuz modules) all share the same TLE epoch and produce zero-distance results. The implementation filters these out by skipping pairs with separation below 0.1km, a threshold that distinguishes docked objects from real conjunctions.

The algorithm is capped at 200 satellites per group to prevent O(n²) computation from timing out requests.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python, FastAPI, SQLAlchemy, Alembic, asyncpg, sgp4, APScheduler |
| **Frontend** | React, CesiumJS, Resium, Vite |
| **Infrastructure** | AWS EC2, AWS S3, AWS CloudFront, Docker, Docker Compose |
| **Testing** | pytest, pytest-asyncio, Jest, React Testing Library (54 tests) |

---

## Running Locally

**Prerequisites:** Docker, Docker Compose, a free [Cesium Ion token](https://cesium.com/ion/tokens)

```bash
git clone https://github.com/cnguyen770/orbital-tracker.git
cd orbital-tracker
cp .env.example .env
# Edit .env with your Cesium Ion token
docker compose up
```

Once running, ingest satellite data:

```bash
curl -X POST "http://localhost:8000/api/satellites/ingest?group=stations"
curl -X POST "http://localhost:8000/api/satellites/ingest?group=weather"
curl -X POST "http://localhost:8000/api/satellites/ingest?group=starlink"
```

Frontend (in a separate terminal):

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`

---

## What I'd Do Differently

**Client-side position propagation.** The current architecture polls the server every 30 seconds for positions. A smoother approach would send TLEs to the browser once and run SGP4 in JavaScript using `satellite.js`, computing positions every frame at 60fps. The tradeoff is more client-side CPU usage.

**Separate database from application server.** PostgreSQL runs as a container on the same EC2 instance as the backend. In production this would move to RDS, a managed service with automated backups and failover.

**Automated deployment.** The CI pipeline runs tests on every push but doesn't deploy. Adding a CD step to GitHub Actions would complete the automation.

---

## Background

The project was inspired by wanting to visualize the satellites constantly passing overhead but invisible to the naked eye. The CMU Wildfire AirSim project involved building UAV simulation tools for low-altitude airspace. This extends that interest to orbital-scale tracking using the same propagation models aerospace organizations use operationally.