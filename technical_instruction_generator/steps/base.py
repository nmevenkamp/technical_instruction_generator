from abc import ABC, abstractmethod

import drawsvg as draw

from ..layout_base import SizedGroup, ViewBox


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
    def view_box(self) -> ViewBox:
        raise NotImplementedError

    @property
    @abstractmethod
    def view_box_closeup(self) -> ViewBox:
        raise NotImplementedError

    @property
    @abstractmethod
    def instruction(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def draw(self, drawing: SizedGroup, x=0, y=0, active: bool = True, dimensions: bool = True) -> None:
        raise NotImplementedError
