"""
The Lineup - FastAPI Backend Application
Main application entry point with routing and middleware configuration.
"""

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI application
app = FastAPI(
    title="The Lineup API",
    description="Fantasy Basketball Draft Assistant - Professional API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js development
        "https://the-lineup.vercel.app",  # Production frontend
        # Add other domains as needed
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Health Check Endpoint
@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """Root endpoint for health checks and API status."""
    return {
        "message": "The Lineup API is running",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Dedicated health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "the-lineup-api",
        "timestamp": "2024-01-01T00:00:00Z"  # Will be dynamic
    }

# API Routes (to be added)
# from app.api.v1.api import api_router
# app.include_router(api_router, prefix="/api/v1")

# Exception Handlers (to be added)
# @app.exception_handler(Exception)
# async def general_exception_handler(request, exc):
#     return JSONResponse(
#         status_code=500,
#         content={"message": "Internal server error"}
#     )

if __name__ == "__main__":
    # Development server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 