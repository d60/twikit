from __future__ import annotations

from typing import Callable


class MockElement:
    def __init__(self, tag_name, document: MockDocument) -> None:
        self.tagName = tag_name
        self.document = document
        self.parentNode: MockElement | None = None

    def appendChild(self, child: MockElement) -> None:
        child.parentNode = self

    def remove(self) -> None:
        self.document.element_seq.remove(self)

    def removeChild(self, child: MockElement) -> None:
        child.remove()

    @property
    def lastElementChild(self) -> MockElement:
        return self.children[-1]

    def setAttribute(self, name: str, value: str) -> None:
        pass

    @property
    def children(self) -> list[MockElement]:
        return self.document._filter_elements(lambda x: x.parentNode == self)


class MockDocument:
    def __init__(self) -> None:
        self.element_seq: list[MockElement] = []
        self.createElement('body')

    def createElement(self, tag_name) -> MockElement:
        element = MockElement(tag_name, self)
        self.element_seq.append(element)
        return element

    def _filter_elements(self, function: Callable[[MockElement], list[MockElement]]) -> list[MockElement]:
        return list(
            filter(
                function,
                self.element_seq
            )
        )

    def getElementsByTagName(self, tag_name):
        return self._filter_elements(lambda x: x.tagName == tag_name)
