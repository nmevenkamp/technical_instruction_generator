from abc import ABC, abstractmethod

from ..layout_base import SizedGroup, ViewBox


class Step(ABC):
    def __init__(self, identifier: str | None = None) -> None:
        self._identifier = identifier

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        raise NotImplementedError

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

    @abstractmethod
    def get_instruction(self, dim_ref_pt: tuple[float, float] | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def draw(
        self,
        group: SizedGroup,
        x=0,
        y=0,
        active: bool = True,
        dimensions: bool = True,
        close_up: bool = False,
        faded: bool = False,
        dim_ref_pt: tuple[float, float] | None = None
    ) -> None:
        raise NotImplementedError
