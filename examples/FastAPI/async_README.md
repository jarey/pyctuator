# Async FastAPI Pyctuator Example

This example demonstrates how to use the async version of Pyctuator with FastAPI and async SQLAlchemy.

## Features

- **Async Support**: Full async/await support throughout the monitoring stack
- **Async Database Health**: Monitor async SQLAlchemy database connections
- **FastAPI Integration**: Seamless integration with FastAPI applications
- **Spring Boot Admin**: Register with Spring Boot Admin for monitoring

## Prerequisites

- Python 3.8+
- Poetry (for dependency management)
- Spring Boot Admin server (optional, for monitoring)

## Installation

1. Install dependencies:
```bash
poetry install
```

2. Install the async SQLAlchemy driver:
```bash
poetry add aiosqlite
```

## Usage

### Running the Application

```bash
poetry run python async_fastapi_example_app.py
```

The application will start on `http://localhost:8000`.

### Available Endpoints

- `GET /` - Application root
- `GET /health` - Application health check
- `GET /database-test` - Test database connectivity
- `GET /pyctuator/health` - Pyctuator health endpoint
- `GET /pyctuator/info` - Application information
- `GET /pyctuator/metrics` - Application metrics
- `GET /pyctuator/env` - Environment variables

### Key Differences from Sync Version

1. **AsyncPyctuator**: Use `AsyncPyctuator` instead of `Pyctuator`
2. **Async Providers**: All health, metrics, and environment providers are async
3. **Async Database**: Uses `AsyncEngine` from SQLAlchemy
4. **Async Endpoints**: All Pyctuator endpoints are async

### Database Health Monitoring

The example includes an `AsyncDbHealthProvider` that monitors the async SQLAlchemy database connection:

```python
from pyctuator.health.async_db_health_provider import AsyncDbHealthProvider

async_db_health_provider = AsyncDbHealthProvider(engine=async_engine, name="async_db")
async_pyctuator.register_health_provider(async_db_health_provider)
```

### Custom Async Providers

You can create custom async providers by implementing the async interfaces:

```python
from pyctuator.health.async_health_provider import AsyncHealthProvider, HealthStatus, Status

class CustomAsyncHealthProvider(AsyncHealthProvider):
    async def get_health(self) -> HealthStatus:
        # Your async health check logic here
        return HealthStatus(status=Status.UP, details=...)
```

## Configuration

The example includes:

- Async database health monitoring
- Memory and thread metrics
- Environment variable monitoring
- Disk space health checks
- Git and build information
- Spring Boot Admin registration

## Spring Boot Admin Integration

If you have a Spring Boot Admin server running, the application will automatically register with it. You can configure the registration URL in the `AsyncPyctuator` constructor.

## Testing

Test the application endpoints:

```bash
# Test the main application
curl http://localhost:8000/

# Test Pyctuator health
curl http://localhost:8000/pyctuator/health

# Test database connectivity
curl http://localhost:8000/database-test
```

## Benefits of Async Support

1. **Non-blocking Operations**: All monitoring operations are non-blocking
2. **Better Performance**: Improved concurrency and resource utilization
3. **Modern Python**: Leverages Python's async/await features
4. **Database Integration**: Native support for async database operations
5. **Scalability**: Better handling of concurrent requests

## Migration from Sync to Async

To migrate from the sync version:

1. Replace `Pyctuator` with `AsyncPyctuator`
2. Update health providers to implement `AsyncHealthProvider`
3. Update metrics providers to implement `AsyncMetricsProvider`
4. Update environment providers to implement `AsyncEnvironmentProvider`
5. Use async database engines and connections
6. Update endpoint handlers to be async where needed 