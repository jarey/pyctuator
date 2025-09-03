"""
Async aiohttp Example with Pyctuator

This example demonstrates how to use AsyncPyctuator with aiohttp and async SQLAlchemy.
"""

import asyncio
import os
from datetime import datetime, timezone

from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from pyctuator.async_pyctuator import AsyncPyctuator
from pyctuator.health.async_db_health_provider import AsyncDbHealthProvider

# Create an async SQLAlchemy engine
async_engine: AsyncEngine = create_async_engine(
    "sqlite+aiosqlite:///./async_aiohttp_example.db",
    echo=True
)

# Create aiohttp app
app = web.Application()

# Initialize AsyncPyctuator
async_pyctuator = AsyncPyctuator(
    app=app,
    app_name="Async aiohttp Pyctuator Example",
    app_url="http://localhost:8080",
    pyctuator_endpoint_url="http://localhost:8080/pyctuator",
    registration_url="http://localhost:8081",  # Spring Boot Admin URL
    app_description="Async aiohttp application with Pyctuator monitoring",
    registration_interval_sec=10,
    free_disk_space_down_threshold_bytes=1024 * 1024 * 100,  # 100MB
    logfile_max_size=10000,
    auto_deregister=True,
    metadata={"async": True, "framework": "aiohttp"},
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
    artifact="async-aiohttp-pyctuator-example",
    group="com.example",
    name="Async aiohttp Pyctuator Example",
    version="1.0.0",
    time=datetime.now(timezone.utc)
)


async def root_handler(request: web.Request) -> web.Response:
    """Root endpoint"""
    return web.json_response({
        "message": "Async aiohttp Pyctuator Example",
        "status": "running",
        "async": True,
        "endpoints": {
            "health": "/pyctuator/health",
            "info": "/pyctuator/info",
            "metrics": "/pyctuator/metrics",
            "env": "/pyctuator/env",
            "loggers": "/pyctuator/loggers"
        }
    })


async def health_handler(request: web.Request) -> web.Response:
    """Application health check"""
    return web.json_response({"status": "healthy", "async": True})


async def database_test_handler(request: web.Request) -> web.Response:
    """Test endpoint to verify database connectivity"""
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute("SELECT 1 as test")
            row = result.fetchone()
            return web.json_response({
                "database": "connected",
                "test_result": row[0] if row else None
            })
    except Exception as e:
        return web.json_response({
            "database": "error",
            "error": str(e)
        })


async def api_data_handler(request: web.Request) -> web.Response:
    """Example API endpoint"""
    return web.json_response({
        "data": "This is some example data from aiohttp",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "async": True
    })


async def cleanup(app: web.Application) -> None:
    """Cleanup on application shutdown"""
    await async_engine.dispose()
    async_pyctuator.stop()


# Add routes
app.router.add_get("/", root_handler)
app.router.add_get("/health", health_handler)
app.router.add_get("/database-test", database_test_handler)
app.router.add_get("/api/data", api_data_handler)

# Add cleanup on shutdown
app.on_cleanup.append(cleanup)

if __name__ == "__main__":
    print("Starting Async aiohttp Pyctuator Example...")
    print("Available endpoints:")
    print("  - GET /                    - Application root")
    print("  - GET /health              - Application health")
    print("  - GET /database-test       - Test database connectivity")
    print("  - GET /api/data            - Example API endpoint")
    print("  - GET /pyctuator/health    - Pyctuator health")
    print("  - GET /pyctuator/info      - Application info")
    print("  - GET /pyctuator/metrics   - Application metrics")
    print("  - GET /pyctuator/env       - Environment variables")
    print("  - GET /pyctuator/loggers   - Logger configuration")
    
    web.run_app(app, host="0.0.0.0", port=8080) 