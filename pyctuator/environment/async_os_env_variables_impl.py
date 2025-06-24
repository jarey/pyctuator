import os
from typing import Dict, Callable

from pyctuator.environment.async_environment_provider import PropertiesSource, PropertyValue, AsyncEnvironmentProvider


class AsyncOsEnvironmentVariableProvider(AsyncEnvironmentProvider):

    async def get_properties_source(self, secret_scrubber: Callable[[Dict], Dict]) -> PropertiesSource:
        scrubbed_env = secret_scrubber(os.environ)  # type: ignore
        properties_dict = {key: PropertyValue(value) for (key, value) in scrubbed_env.items()}
        return PropertiesSource("systemEnvironment", properties_dict) 