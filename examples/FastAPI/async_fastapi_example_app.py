import asyncio
import os
from datetime import datetime, timezone

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from pyctuator.async_pyctuator import AsyncPyctuator
from pyctuator.health.async_db_health_provider import AsyncDbHealthProvider

app = FastAPI(title="Async FastAPI Pyctuator Example")

# Create an async SQLAlchemy engine
# Note: This is a mock engine for demonstration. In a real application, you would use a real database URL
async_engine: AsyncEngine = create_async_engine(
    "sqlite+aiosqlite:///./async_example.db",
    echo=True
)

# Initialize AsyncPyctuator with async database health provider
async_pyctuator = AsyncPyctuator(
    app=app,
    app_name="Async FastAPI Pyctuator Example",
    app_url="http://localhost:8000",
    pyctuator_endpoint_url="http://localhost:8000/pyctuator",
    registration_url="http://localhost:8080",  # Spring Boot Admin URL
    app_description="Async FastAPI application with Pyctuator monitoring",
    registration_interval_sec=10,
    free_disk_space_down_threshold_bytes=1024 * 1024 * 100,  # 100MB
    logfile_max_size=10000,
    auto_deregister=True,
    metadata={"async": True, "framework": "fastapi"},
    additional_app_info={
        "async_support": True,
        "database": "sqlite+aiosqlite",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
)

# Register async database health provider
async_db_health_provider = AsyncDbHealthProvider(engine=async_engine, name="async_db")
async_pyctuator.register_health_provider(async_db_health_provider)

# Set git and build information
async_pyctuator.set_git_info(
    commit="abc123",
    time=datetime.now(timezone.utc),
    branch="main"
)

async_pyctuator.set_build_info(
    artifact="async-fastapi-pyctuator-example",
    group="com.example",
    name="Async FastAPI Pyctuator Example",
    version="1.0.0",
    time=datetime.now(timezone.utc)
)


@app.get("/")
async def root():
    return {"message": "Async FastAPI Pyctuator Example", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy", "async": True}


@app.get("/database-test")
async def database_test():
    """Test endpoint to verify database connectivity"""
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute("SELECT 1 as test")
            row = result.fetchone()
            return {"database": "connected", "test_result": row[0] if row else None}
    except Exception as e:
        return {"database": "error", "error": str(e)}


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    await async_engine.dispose()
    async_pyctuator.stop()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 