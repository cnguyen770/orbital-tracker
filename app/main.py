from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import satellites

app = FastAPI(
    title="Orbital Tracker",
    description="Real-time satellite tracking and orbital analysis.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(satellites.router, prefix="/api/satellites", tags=["satellites"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}