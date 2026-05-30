from abc import ABC, abstractmethod
from typing import Any

from changelens.schemas.event import EventCreate


class IngestionParser(ABC):
    @property
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    def parse(self, payload: dict[str, Any], headers: dict[str, str]) -> EventCreate: ...
