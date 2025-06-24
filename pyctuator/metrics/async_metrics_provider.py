from abc import ABC, abstractmethod

from typing import List

from pyctuator.metrics.metrics_provider import Metric, MetricNames, Measurement, MetricTag


class AsyncMetricsProvider(ABC):

    @abstractmethod
    def get_prefix(self) -> str:
        pass

    @abstractmethod
    def get_supported_metric_names(self) -> List[str]:
        pass

    @abstractmethod
    async def get_metric(self, metric_name: str) -> Metric:
        pass 