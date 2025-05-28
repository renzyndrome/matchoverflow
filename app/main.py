from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

from .models.database import engine, Base
from .routes import auth, users, matching
from .config import APP_NAME, APP_VERSION, ALLOWED_ORIGINS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="AI-powered student matching platform"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log the validation error details
    logger.error(f"Validation error on {request.url.path}")
    logger.error(f"Request body: {await request.body()}")
    logger.error(f"Validation errors: {exc.errors()}")
    
    # Return a detailed error response
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(matching.router)

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("app/templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard():
    with open("app/templates/dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/matching", response_class=HTMLResponse)
async def read_matching():
    with open("app/templates/matching.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/profile", response_class=HTMLResponse)
async def read_profile():
    with open("app/templates/profile.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": APP_VERSION} 