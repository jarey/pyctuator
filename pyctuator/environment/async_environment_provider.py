from abc import ABC, abstractmethod

from typing import Callable, Dict

from pyctuator.environment.environment_provider import PropertyValue, PropertiesSource, EnvironmentData


class AsyncEnvironmentProvider(ABC):

    @abstractmethod
    async def get_properties_source(self, secret_scrubber: Callable[[Dict], Dict]) -> PropertiesSource:
        pass 