# Async Pyctuator Implementation

This document describes the async implementation of Pyctuator, which provides full async/await support for monitoring and health checks in Python applications.

## Overview

The async implementation provides the same functionality as the original sync Pyctuator but with full async/await support throughout the entire monitoring stack. This enables better performance, non-blocking operations, and seamless integration with modern async Python applications.

## Key Features

- **Full Async Support**: All health checks, metrics collection, and environment monitoring are async
- **Async Database Integration**: Native support for async SQLAlchemy engines and connections
- **FastAPI Integration**: Seamless integration with FastAPI applications
- **Non-blocking Operations**: All monitoring operations are non-blocking
- **Backward Compatibility**: Maintains the same API structure as the sync version

## Architecture

### Async Interfaces

The async implementation introduces new async interfaces that mirror the sync ones:

#### AsyncHealthProvider
```python
from pyctuator.health.async_health_provider import AsyncHealthProvider, HealthStatus, Status

class CustomAsyncHealthProvider(AsyncHealthProvider):
    async def get_health(self) -> HealthStatus:
        # Your async health check logic here
        return HealthStatus(status=Status.UP, details=...)
```

#### AsyncMetricsProvider
```python
from pyctuator.metrics.async_metrics_provider import AsyncMetricsProvider, Metric

class CustomAsyncMetricsProvider(AsyncMetricsProvider):
    async def get_metric(self, metric_name: str) -> Metric:
        # Your async metrics collection logic here
        return Metric(...)
```

#### AsyncEnvironmentProvider
```python
from pyctuator.environment.async_environment_provider import AsyncEnvironmentProvider, PropertiesSource

class CustomAsyncEnvironmentProvider(AsyncEnvironmentProvider):
    async def get_properties_source(self, secret_scrubber) -> PropertiesSource:
        # Your async environment data collection logic here
        return PropertiesSource(...)
```

### Core Components

#### AsyncPyctuator
The main entry point for async applications:

```python
from pyctuator.async_pyctuator import AsyncPyctuator

async_pyctuator = AsyncPyctuator(
    app=app,
    app_name="My Async App",
    app_url="http://localhost:8000",
    pyctuator_endpoint_url="http://localhost:8000/pyctuator",
    registration_url="http://localhost:8080"
)
```

#### AsyncPyctuatorImpl
The core implementation that manages async providers and handles async operations.

#### AsyncFastApiPyctuator
FastAPI-specific integration that provides async endpoints.

## Built-in Async Providers

### AsyncDbHealthProvider
Monitors async SQLAlchemy database connections:

```python
from pyctuator.health.async_db_health_provider import AsyncDbHealthProvider
from sqlalchemy.ext.asyncio import create_async_engine

async_engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
db_health_provider = AsyncDbHealthProvider(engine=async_engine, name="async_db")
async_pyctuator.register_health_provider(db_health_provider)
```

### AsyncMemoryMetricsProvider
Collects memory metrics asynchronously:

```python
from pyctuator.metrics.async_memory_metrics_impl import AsyncMemoryMetricsProvider

memory_provider = AsyncMemoryMetricsProvider()
async_pyctuator.register_metrics_provider(memory_provider)
```

### AsyncThreadMetricsProvider
Collects thread metrics asynchronously:

```python
from pyctuator.metrics.async_thread_metrics_impl import AsyncThreadMetricsProvider

thread_provider = AsyncThreadMetricsProvider()
async_pyctuator.register_metrics_provider(thread_provider)
```

### AsyncDiskSpaceHealthProvider
Monitors disk space asynchronously:

```python
from pyctuator.health.async_diskspace_health_impl import AsyncDiskSpaceHealthProvider

disk_provider = AsyncDiskSpaceHealthProvider(free_bytes_down_threshold=1024*1024*100)
async_pyctuator.register_health_provider(disk_provider)
```

### AsyncOsEnvironmentVariableProvider
Collects environment variables asynchronously:

```python
from pyctuator.environment.async_os_env_variables_impl import AsyncOsEnvironmentVariableProvider

env_provider = AsyncOsEnvironmentVariableProvider()
async_pyctuator.register_environment_provider(env_provider)
```

## Usage Examples

### FastAPI Application with Async Database

```python
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from pyctuator.async_pyctuator import AsyncPyctuator
from pyctuator.health.async_db_health_provider import AsyncDbHealthProvider

app = FastAPI()

# Create async database engine
async_engine = create_async_engine("sqlite+aiosqlite:///./app.db")

# Initialize AsyncPyctuator
async_pyctuator = AsyncPyctuator(
    app=app,
    app_name="Async FastAPI App",
    app_url="http://localhost:8000",
    pyctuator_endpoint_url="http://localhost:8000/pyctuator",
    registration_url="http://localhost:8080"
)

# Register async database health provider
db_health = AsyncDbHealthProvider(engine=async_engine, name="async_db")
async_pyctuator.register_health_provider(db_health)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.on_event("shutdown")
async def shutdown():
    await async_engine.dispose()
    async_pyctuator.stop()
```

### Custom Async Health Provider

```python
import aiohttp
from pyctuator.health.async_health_provider import AsyncHealthProvider, HealthStatus, Status, HealthDetails

class ExternalServiceHealthProvider(AsyncHealthProvider):
    def __init__(self, service_url: str, name: str = "external_service"):
        self.service_url = service_url
        self.name = name

    def is_supported(self) -> bool:
        return True

    def get_name(self) -> str:
        return self.name

    async def get_health(self) -> HealthStatus:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.service_url) as response:
                    if response.status == 200:
                        return HealthStatus(status=Status.UP, details=HealthDetails())
                    else:
                        return HealthStatus(status=Status.DOWN, details=HealthDetails())
        except Exception:
            return HealthStatus(status=Status.DOWN, details=HealthDetails())

# Register the custom provider
external_health = ExternalServiceHealthProvider("https://api.example.com/health")
async_pyctuator.register_health_provider(external_health)
```

### Custom Async Metrics Provider

```python
import asyncio
from pyctuator.metrics.async_metrics_provider import AsyncMetricsProvider, Metric, Measurement

class AsyncCustomMetricsProvider(AsyncMetricsProvider):
    def __init__(self):
        self.counter = 0

    def get_prefix(self) -> str:
        return "custom"

    def get_supported_metric_names(self) -> List[str]:
        return ["custom.requests", "custom.active_connections"]

    async def get_metric(self, metric_name: str) -> Metric:
        if metric_name == "custom.requests":
            self.counter += 1
            return Metric(
                name=metric_name,
                description="Total requests processed",
                baseUnit="requests",
                measurements=[Measurement("COUNT", self.counter)],
                availableTags=[]
            )
        elif metric_name == "custom.active_connections":
            # Simulate async operation
            await asyncio.sleep(0.001)
            return Metric(
                name=metric_name,
                description="Active connections",
                baseUnit="connections",
                measurements=[Measurement("VALUE", 42.0)],
                availableTags=[]
            )
        else:
            raise KeyError(f"Unknown metric {metric_name}")

# Register the custom provider
custom_metrics = AsyncCustomMetricsProvider()
async_pyctuator.register_metrics_provider(custom_metrics)
```

## Migration from Sync to Async

### Step 1: Replace Pyctuator with AsyncPyctuator
```python
# Before
from pyctuator import Pyctuator
pyctuator = Pyctuator(...)

# After
from pyctuator.async_pyctuator import AsyncPyctuator
async_pyctuator = AsyncPyctuator(...)
```

### Step 2: Update Health Providers
```python
# Before
from pyctuator.health.health_provider import HealthProvider
class MyHealthProvider(HealthProvider):
    def get_health(self) -> HealthStatus:
        return HealthStatus(...)

# After
from pyctuator.health.async_health_provider import AsyncHealthProvider
class MyAsyncHealthProvider(AsyncHealthProvider):
    async def get_health(self) -> HealthStatus:
        return HealthStatus(...)
```

### Step 3: Update Metrics Providers
```python
# Before
from pyctuator.metrics.metrics_provider import MetricsProvider
class MyMetricsProvider(MetricsProvider):
    def get_metric(self, metric_name: str) -> Metric:
        return Metric(...)

# After
from pyctuator.metrics.async_metrics_provider import AsyncMetricsProvider
class MyAsyncMetricsProvider(AsyncMetricsProvider):
    async def get_metric(self, metric_name: str) -> Metric:
        return Metric(...)
```

### Step 4: Update Environment Providers
```python
# Before
from pyctuator.environment.environment_provider import EnvironmentProvider
class MyEnvironmentProvider(EnvironmentProvider):
    def get_properties_source(self, secret_scrubber) -> PropertiesSource:
        return PropertiesSource(...)

# After
from pyctuator.environment.async_environment_provider import AsyncEnvironmentProvider
class MyAsyncEnvironmentProvider(AsyncEnvironmentProvider):
    async def get_properties_source(self, secret_scrubber) -> PropertiesSource:
        return PropertiesSource(...)
```

### Step 5: Update Database Connections
```python
# Before
from sqlalchemy import create_engine
engine = create_engine("postgresql://user:pass@localhost/db")

# After
from sqlalchemy.ext.asyncio import create_async_engine
async_engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
```

## Benefits

1. **Performance**: Non-blocking operations improve overall application performance
2. **Scalability**: Better handling of concurrent requests and operations
3. **Modern Python**: Leverages Python's async/await features
4. **Database Integration**: Native support for async database operations
5. **Resource Efficiency**: Better resource utilization with async I/O

## Limitations

1. **Framework Support**: Currently only supports FastAPI (other frameworks can be added)
2. **Provider Compatibility**: Sync providers cannot be used with AsyncPyctuator
3. **Learning Curve**: Requires understanding of async/await patterns

## Testing

Run the async tests:

```bash
pytest tests/test_async_pyctuator.py -v
```

## Examples

See the `examples/FastAPI/async_fastapi_example_app.py` for a complete working example.

## Contributing

When adding new async providers or features:

1. Follow the async interface patterns established
2. Ensure all operations are non-blocking
3. Add appropriate tests
4. Update documentation

## Future Enhancements

- Support for other async web frameworks (aiohttp, Starlette, etc.)
- Async Redis health provider
- Async HTTP client health provider
- Async cache health provider
- Performance monitoring and profiling 