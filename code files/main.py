"""
LegalEase API
=============
Backend entry point for LegalEase, an AI-powered legal document generator
built with FastAPI.

What this file does:
    1. Creates the FastAPI application.
    2. Configures CORS so a frontend (e.g. Streamlit) can call the API.
    3. Registers the endpoints defined in routes.py.
    4. Exposes utility endpoints: "/" (info) and "/health" (liveness check).

Run locally:
    uvicorn main:app --reload --port 8000

Auto-generated docs:
    Swagger UI -> http://localhost:8000/docs
    ReDoc      -> http://localhost:8000/redoc
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import router  # Router with the document-generation endpoints

# --- Application setup -------------------------------------------------------
app = FastAPI(
    title="LegalEase API",
    description="AI-powered legal document generator",
    version="1.0.0",
)

# --- Middleware --------------------------------------------------------------
# CORS controls which browser origins may call this API.
# WARNING: "*" allows every origin. Use it for development only.
# In production, set your exact frontend URL,
# e.g. ["https://yourapp.streamlit.app"].
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Allowed origins
    allow_credentials=True,   # Allow cookies / Authorization headers
    allow_methods=["*"],      # Allowed HTTP methods
    allow_headers=["*"],      # Allowed request headers
)

# --- Routers -----------------------------------------------------------------
# Adds all endpoints from routes.py (e.g. POST /generate).
app.include_router(router)


# --- Utility endpoints -------------------------------------------------------
@app.get("/")
def root():
    """
    Root endpoint with basic service information.

    Returns:
        dict: Service name, status, docs URL and the main generate endpoint.
    """
    return {
        "name": "LegalEase",
        "status": "running",
        "docs": "/docs",
        "generate_endpoint": "POST /generate",
    }


@app.get("/health")
def health():
    """
    Liveness check for the server.

    Used by Docker, Render, Railway, Kubernetes or uptime monitors to
    confirm the process is running.

    Returns:
        dict: {"status": "ok"} when the server is responding.
    """
    return {"status": "ok"}
