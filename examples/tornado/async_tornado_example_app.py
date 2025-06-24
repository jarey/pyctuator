"""
Async Tornado Example with Pyctuator

This example demonstrates how to use AsyncPyctuator with Tornado and async SQLAlchemy.
"""

import asyncio
import json
import os
from datetime import datetime, timezone

from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from pyctuator.async_pyctuator import AsyncPyctuator
from pyctuator.health.async_db_health_provider import AsyncDbHealthProvider

# Create an async SQLAlchemy engine
async_engine: AsyncEngine = create_async_engine(
    "sqlite+aiosqlite:///./async_tornado_example.db",
    echo=True
)

# Create Tornado app
app = Application()

# Initialize AsyncPyctuator
async_pyctuator = AsyncPyctuator(
    app=app,
    app_name="Async Tornado Pyctuator Example",
    app_url="http://localhost:8888",
    pyctuator_endpoint_url="http://localhost:8888/pyctuator",
    registration_url="http://localhost:8081",  # Spring Boot Admin URL
    app_description="Async Tornado application with Pyctuator monitoring",
    registration_interval_sec=10,
    free_disk_space_down_threshold_bytes=1024 * 1024 * 100,  # 100MB
    logfile_max_size=10000,
    auto_deregister=True,
    metadata={"async": True, "framework": "tornado"},
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
    artifact="async-tornado-pyctuator-example",
    group="com.example",
    name="Async Tornado Pyctuator Example",
    version="1.0.0",
    time=datetime.now(timezone.utc)
)


class RootHandler(RequestHandler):
    """Root endpoint"""
    
    def get(self):
        self.write({
            "message": "Async Tornado Pyctuator Example",
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


class HealthHandler(RequestHandler):
    """Application health check"""
    
    def get(self):
        self.write({"status": "healthy", "async": True})


class DatabaseTestHandler(RequestHandler):
    """Test endpoint to verify database connectivity"""
    
    async def get(self):
        try:
            async with async_engine.begin() as conn:
                result = await conn.execute("SELECT 1 as test")
                row = result.fetchone()
                self.write({
                    "database": "connected",
                    "test_result": row[0] if row else None
                })
        except Exception as e:
            self.write({
                "database": "error",
                "error": str(e)
            })


class ApiDataHandler(RequestHandler):
    """Example API endpoint"""
    
    def get(self):
        self.write({
            "data": "This is some example data from Tornado",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "async": True
        })


async def cleanup():
    """Cleanup on application shutdown"""
    await async_engine.dispose()
    async_pyctuator.stop()


# Add routes
app.add_handlers(r".*", [
    (r"/", RootHandler),
    (r"/health", HealthHandler),
    (r"/database-test", DatabaseTestHandler),
    (r"/api/data", ApiDataHandler),
])

# Add cleanup on shutdown
IOLoop.current().add_callback(cleanup)

if __name__ == "__main__":
    print("Starting Async Tornado Pyctuator Example...")
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
    
    app.listen(8888)
    print("Server started on http://localhost:8888")
    IOLoop.current().start() 