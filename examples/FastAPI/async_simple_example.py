"""
Simple Async FastAPI Example with Pyctuator

This example demonstrates the basic usage of AsyncPyctuator with FastAPI.
It doesn't require any external database or services.
"""

from datetime import datetime, timezone
from fastapi import FastAPI

from pyctuator.async_pyctuator import AsyncPyctuator

# Create FastAPI app
app = FastAPI(title="Simple Async Pyctuator Example")

# Initialize AsyncPyctuator
async_pyctuator = AsyncPyctuator(
    app=app,
    app_name="Simple Async Pyctuator Example",
    app_url="http://localhost:8000",
    pyctuator_endpoint_url="http://localhost:8000/pyctuator",
    registration_url=None,  # No Spring Boot Admin registration for this example
    app_description="Simple FastAPI application with async Pyctuator monitoring",
    registration_interval_sec=10,
    free_disk_space_down_threshold_bytes=1024 * 1024 * 100,  # 100MB
    logfile_max_size=10000,
    auto_deregister=True,
    metadata={"async": True, "framework": "fastapi", "example": "simple"},
    additional_app_info={
        "async_support": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "features": ["health", "metrics", "environment", "logging"]
    }
)

# Set git and build information
async_pyctuator.set_git_info(
    commit="abc123",
    time=datetime.now(timezone.utc),
    branch="main"
)

async_pyctuator.set_build_info(
    artifact="simple-async-pyctuator-example",
    group="com.example",
    name="Simple Async Pyctuator Example",
    version="1.0.0",
    time=datetime.now(timezone.utc)
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Simple Async Pyctuator Example",
        "status": "running",
        "async": True,
        "endpoints": {
            "health": "/pyctuator/health",
            "info": "/pyctuator/info",
            "metrics": "/pyctuator/metrics",
            "env": "/pyctuator/env",
            "loggers": "/pyctuator/loggers"
        }
    }


@app.get("/health")
async def health():
    """Application health check"""
    return {"status": "healthy", "async": True}


@app.get("/api/data")
async def get_data():
    """Example API endpoint"""
    return {
        "data": "This is some example data",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "async": True
    }


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    async_pyctuator.stop()


if __name__ == "__main__":
    import uvicorn
    print("Starting Simple Async Pyctuator Example...")
    print("Available endpoints:")
    print("  - GET /                    - Application root")
    print("  - GET /health              - Application health")
    print("  - GET /api/data            - Example API endpoint")
    print("  - GET /pyctuator/health    - Pyctuator health")
    print("  - GET /pyctuator/info      - Application info")
    print("  - GET /pyctuator/metrics   - Application metrics")
    print("  - GET /pyctuator/env       - Environment variables")
    print("  - GET /pyctuator/loggers   - Logger configuration")
    print("\nOpen http://localhost:8000/docs for API documentation")
    
    uvicorn.run(app, host="0.0.0.0", port=8000) 