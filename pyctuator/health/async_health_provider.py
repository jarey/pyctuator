import abc
from abc import ABC

from pyctuator.health.health_provider import HealthDetails, HealthStatus, HealthSummary, Status


class AsyncHealthProvider(ABC):
    @abc.abstractmethod
    def is_supported(self) -> bool:
        pass

    @abc.abstractmethod
    def get_name(self) -> str:
        pass

    @abc.abstractmethod
    async def get_health(self) -> HealthStatus:
        pass 