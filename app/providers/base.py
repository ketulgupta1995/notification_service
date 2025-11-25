from typing import Protocol, Dict, Any
from abc import ABC, abstractmethod


class Provider(ABC):
    name: str


@abstractmethod
async def send(self, user: Dict[str, Any], subject: str | None, body: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Send the notification. Return a dict with status and provider_response."""
    raise NotImplementedError