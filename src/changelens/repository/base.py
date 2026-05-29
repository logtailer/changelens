from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    async def get(self, id: UUID) -> T | None: ...

    @abstractmethod
    async def create(self, obj: T) -> T: ...

    @abstractmethod
    async def list(self, **filters: object) -> tuple[list[T], int]: ...
