import pytest
import asyncio
from typing import List
from unittest.mock import AsyncMock, MagicMock

from pyctuator.async_pyctuator import AsyncPyctuator
from pyctuator.health.async_health_provider import AsyncHealthProvider, HealthStatus, Status, HealthDetails
from pyctuator.metrics.async_metrics_provider import AsyncMetricsProvider, Metric, Measurement
from pyctuator.environment.async_environment_provider import AsyncEnvironmentProvider, PropertiesSource, PropertyValue


class MockAsyncHealthProvider(AsyncHealthProvider):
    def __init__(self, name: str = "mock", status: Status = Status.UP):
        self.name = name
        self.status = status

    def is_supported(self) -> bool:
        return True

    def get_name(self) -> str:
        return self.name

    async def get_health(self) -> HealthStatus:
        return HealthStatus(status=self.status, details=HealthDetails())


class MockAsyncMetricsProvider(AsyncMetricsProvider):
    def __init__(self, prefix: str = "mock"):
        self.prefix = prefix

    def get_prefix(self) -> str:
        return self.prefix

    def get_supported_metric_names(self) -> List[str]:
        return [f"{self.prefix}.test"]

    async def get_metric(self, metric_name: str) -> Metric:
        return Metric(
            name=metric_name,
            description="Test metric",
            baseUnit="count",
            measurements=[Measurement("VALUE", 1.0)],
            availableTags=[]
        )


class MockAsyncEnvironmentProvider(AsyncEnvironmentProvider):
    async def get_properties_source(self, secret_scrubber):
        return PropertiesSource(
            name="test",
            properties={"test.key": PropertyValue("test.value")}
        )


@pytest.mark.asyncio
async def test_async_health_provider():
    """Test that async health providers work correctly"""
    provider = MockAsyncHealthProvider("test", Status.UP)
    
    assert provider.is_supported() is True
    assert provider.get_name() == "test"
    
    health = await provider.get_health()
    assert health.status == Status.UP
    assert isinstance(health.details, HealthDetails)


@pytest.mark.asyncio
async def test_async_metrics_provider():
    """Test that async metrics providers work correctly"""
    provider = MockAsyncMetricsProvider("test")
    
    assert provider.get_prefix() == "test"
    assert provider.get_supported_metric_names() == ["test.test"]
    
    metric = await provider.get_metric("test.test")
    assert metric.name == "test.test"
    assert metric.description == "Test metric"
    assert len(metric.measurements) == 1
    assert metric.measurements[0].value == 1.0


@pytest.mark.asyncio
async def test_async_environment_provider():
    """Test that async environment providers work correctly"""
    provider = MockAsyncEnvironmentProvider()
    
    properties_source = await provider.get_properties_source(lambda x: x)
    assert properties_source.name == "test"
    assert "test.key" in properties_source.properties
    assert properties_source.properties["test.key"].value == "test.value"


@pytest.mark.asyncio
async def test_async_pyctuator_impl_health():
    """Test that AsyncPyctuatorImpl correctly handles async health providers"""
    from pyctuator.impl.async_pyctuator_impl import AsyncPyctuatorImpl, AppInfo, AppDetails
    
    app_info = AppInfo(app=AppDetails(name="test", description="test"))
    impl = AsyncPyctuatorImpl(
        app_info=app_info,
        pyctuator_endpoint_url="http://localhost:8000/pyctuator",
        logfile_max_size=1000,
        logfile_formatter="%(message)s",
        additional_app_info=None,
        disabled_endpoints=set()
    )
    
    # Register a health provider
    provider = MockAsyncHealthProvider("test", Status.UP)
    impl.register_health_providers(provider)
    
    # Get health summary
    health_summary = await impl.get_health()
    assert health_summary.status == Status.UP
    assert "test" in health_summary.details
    assert health_summary.details["test"].status == Status.UP


@pytest.mark.asyncio
async def test_async_pyctuator_impl_metrics():
    """Test that AsyncPyctuatorImpl correctly handles async metrics providers"""
    from pyctuator.impl.async_pyctuator_impl import AsyncPyctuatorImpl, AppInfo, AppDetails
    
    app_info = AppInfo(app=AppDetails(name="test", description="test"))
    impl = AsyncPyctuatorImpl(
        app_info=app_info,
        pyctuator_endpoint_url="http://localhost:8000/pyctuator",
        logfile_max_size=1000,
        logfile_formatter="%(message)s",
        additional_app_info=None,
        disabled_endpoints=set()
    )
    
    # Register a metrics provider
    provider = MockAsyncMetricsProvider("test")
    impl.register_metrics_provider(provider)
    
    # Get metric names
    metric_names = impl.get_metric_names()
    assert "test.test" in metric_names.names
    
    # Get metric measurement
    metric = await impl.get_metric_measurement("test.test")
    assert metric.name == "test.test"


@pytest.mark.asyncio
async def test_async_pyctuator_impl_environment():
    """Test that AsyncPyctuatorImpl correctly handles async environment providers"""
    from pyctuator.impl.async_pyctuator_impl import AsyncPyctuatorImpl, AppInfo, AppDetails
    
    app_info = AppInfo(app=AppDetails(name="test", description="test"))
    impl = AsyncPyctuatorImpl(
        app_info=app_info,
        pyctuator_endpoint_url="http://localhost:8000/pyctuator",
        logfile_max_size=1000,
        logfile_formatter="%(message)s",
        additional_app_info=None,
        disabled_endpoints=set()
    )
    
    # Register an environment provider
    provider = MockAsyncEnvironmentProvider()
    impl.register_environment_provider(provider)
    
    # Get environment data
    env_data = await impl.get_environment()
    assert len(env_data.propertySources) == 1
    assert env_data.propertySources[0].name == "test" 