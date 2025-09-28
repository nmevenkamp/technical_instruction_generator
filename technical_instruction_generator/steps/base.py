from abc import ABC, abstractmethod

from drawsvg import Drawing


class Step(ABC):
    @property
    @abstractmethod
    def size(self) -> tuple[int, int]:
        raise NotImplementedError

    @property
    @abstractmethod
    def instruction(self) -> str:
        return NotImplemented

    @abstractmethod
    def draw(self, drawing: Drawing, active: bool = True) -> None:
        raise NotImplementedError
