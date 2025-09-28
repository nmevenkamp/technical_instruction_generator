from abc import ABC, abstractmethod

from drawsvg import Drawing, Group


class Step(ABC):
    def __init__(self, name: str | None = None) -> None:
        self._identifier = name

    @property
    def identifier(self) -> str | None:
        return self._identifier

    @identifier.setter
    def identifier(self, identifier: str) -> None:
        self._identifier = identifier

    @property
    @abstractmethod
    def size(self) -> tuple[int, int]:
        raise NotImplementedError

    @property
    @abstractmethod
    def instruction(self) -> str:
        return NotImplemented

    @abstractmethod
    def draw(self, drawing: Drawing | Group, active: bool = True) -> None:
        raise NotImplementedError
