"""
OmniWatch 2.0 — Integration
Component: BaseIntegration (Abstract Base Class)
Layer: Integration
Phase: 7
Purpose: Abstract base class defining the contract for all 25+ integrations
Inputs: Integration-specific configuration dict
Outputs: Standardized metric dictionaries and health status
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseIntegration(ABC):
    """Abstract base class for all OmniWatch integrations.

    Every integration must implement collect_metrics() and health_check().
    The to_kafka() method provides a default Kafka publishing path.
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__

    @abstractmethod
    def collect_metrics(self) -> list[dict]:
        """Collect metrics from the integrated system.

        Returns a list of metric dictionaries conforming to OmniWatch's
        telemetry schema.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check whether the integrated system is reachable.

        Returns True if the connection is healthy, False otherwise.
        """
        pass

    def to_kafka(self, metrics: list[dict], topic: str) -> None:
        """Publish collected metrics to a Kafka topic.

        Default implementation is a no-op; subclasses should override
        with a real Kafka producer once the broker connection is wired.
        """
        pass
