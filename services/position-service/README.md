# Position Service

A Java/Spring Boot microservice that handles SGP4 orbital position computation for the orbital tracker. The main Python backend delegates the CPU-intensive propagation work here over REST when `POSITION_SERVICE_URL` is configured, and falls back to computing inline when it isn't.

The reason this exists as a separate service: SGP4 is pure CPU-bound math. Isolating it means the computation can scale independently of the API layer, and it gave me a real reason to build a second backend in a different language rather than rewriting something that already worked.

---

## Endpoints

- `POST /position` — single TLE in, geodetic position out
- `POST /positions/batch` — list of TLEs in, list of positions out (capped at 1000). This is the endpoint the Python backend actually uses, since batching avoids paying HTTP overhead per satellite
- `GET /health` — liveness check

Example:

```bash
curl -X POST http://localhost:8080/position \
  -H "Content-Type: application/json" \
  -d '{
    "tleLine1": "1 25544U 98067A   24001.50000000  .00016717  00000-0  10270-3 0  9000",
    "tleLine2": "2 25544  51.6400 208.9163 0006317  69.9862  25.2906 15.49560532428342"
  }'
```

Response:

```json
{
  "noradId": "25544",
  "latitude": 47.1,
  "longitude": -122.6,
  "altitudeKm": 421.3,
  "timestamp": "2026-06-11T18:30:00Z"
}
```

---

## The SGP4 implementation

The propagation math comes from the reference SGP4 implementation by David Vallado, via the Java port at [aholinch/sgp4](https://github.com/aholinch/sgp4). The source files are vendored into `src/main/java/sgp4/` rather than pulled as a dependency — the port isn't published to Maven Central, and vendoring the public-domain reference code keeps the build self-contained. This mirrors how the Python ecosystem handles it (the `sgp4` pip package is the same Vallado code).

The TEME-to-geodetic conversion (GMST rotation, then iterative WGS84 transform) is implemented in `Sgp4Service` and mirrors the Python backend's math, which makes cross-validation between the two implementations straightforward.

I considered Orekit, which is the heavyweight option on Maven Central, but it pulls in a full astrodynamics stack and requires loading an external data file at runtime. For a service that does exactly one thing, the vendored reference implementation is the better fit.

---

## Setup

Requires Java 21. The vendored SGP4 files need to be copied in before the first build:

```bash
# from services/position-service
mkdir -p src/main/java/sgp4
# copy SGP4.java, TLE.java, ElsetRec.java from
# https://github.com/aholinch/sgp4 (src/java folder)
# into src/main/java/sgp4/
```

Then:

```bash
./gradlew test       # run the test suite
./gradlew bootRun    # start on :8080
curl localhost:8080/health
```

Or with Docker:

```bash
docker build -t position-service .
docker run -p 8080:8080 position-service
```

---

## How the Python backend uses it

When `POSITION_SERVICE_URL` is set, the Python backend's position computation path calls `POST /positions/batch` here instead of running SGP4 inline. When unset, it computes inline exactly as before — the integration is feature-flagged, so the system degrades gracefully if this service is down and the existing test suite runs without it.

Redis caching stays in the Python layer either way. This service is stateless: TLEs in, positions out.
