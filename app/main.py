"""
FastAPI application — the main entry point.
Exposes POST /api/interview and serves the frontend.
"""

import json
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.models import InterviewRequest, InterviewResponse
from app.interview_engine import InterviewEngine
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
CANDIDATES_PATH = BASE_DIR / "problem_files" / "candidates.json"

# Interview engine (singleton)
engine = InterviewEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    logger.info("🚀 AI Interview Agent starting up")
    logger.info("   Model: %s", settings.MODEL_NAME)
    logger.info("   Min questions: %d | Min topics: %d | Max questions: %d",
                settings.MIN_QUESTIONS, settings.MIN_TOPICS, settings.MAX_QUESTIONS)
    yield
    logger.info("👋 AI Interview Agent shutting down")


app = FastAPI(
    title="AI Interview Agent",
    description="Personalized technical interview agent for AI Cohort candidates",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API Endpoints ---

@app.post("/api/interview", response_model=InterviewResponse)
async def interview(request: InterviewRequest):
    """
    Main interview endpoint.
    - With `candidate`: starts a new interview
    - With `message`: continues an existing interview
    """
    try:
        if request.candidate is not None:
            # Start new interview
            logger.info("Starting interview: session=%s, candidate=%s",
                        request.sessionId, request.candidate.member.name)
            response = await engine.start_interview(
                session_id=request.sessionId,
                candidate=request.candidate,
            )
            return response

        elif request.message is not None:
            # Continue interview
            logger.info("Interview turn: session=%s", request.sessionId)
            response = await engine.handle_turn(
                session_id=request.sessionId,
                message=request.message,
            )
            return response

        else:
            raise HTTPException(
                status_code=400,
                detail="Request must include either 'candidate' (to start) or 'message' (to continue)",
            )

    except RuntimeError as e:
        logger.error("Interview error: %s", e)
        raise HTTPException(status_code=503, detail=str(e))

    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "model": settings.MODEL_NAME}


@app.get("/api/candidates")
async def get_candidates():
    """Return the list of candidates for the frontend selector."""
    try:
        with open(CANDIDATES_PATH, "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Candidates file not found")


# --- Static Files (Frontend) ---

@app.get("/")
async def serve_frontend():
    """Serve the main frontend page."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse(
        {"message": "AI Interview Agent API is running. Frontend not found."},
        status_code=200,
    )


# Mount static files for CSS/JS
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# --- Run with Uvicorn ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
