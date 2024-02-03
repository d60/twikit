from __future__ import annotations

from typing import Any, Awaitable, Generic, Iterator, TypeVar
from urllib import parse

T = TypeVar('T')


class Result(Generic[T]):
    """
    This class is designed to store multiple results.
    The `next` method can be used to retrieve further results.
    As with a regular list, you can access elements by
    specifying indexes and iterate over elements using a for loop.

    Attributes
    ----------
    token : str
        Token used to obtain the next result.
    """

    def __init__(
        self,
        results: list[T],
        fetch_next_result: Awaitable | None = None,
        token: str | None = None
    ) -> None:
        self.__results = results
        self.token = token
        self.__fetch_next_result = fetch_next_result

    async def next(self) -> Result[T]:
        """
        The next result.
        """
        if self.__fetch_next_result is None:
            return Result([])
        return await self.__fetch_next_result()

    def __iter__(self) -> Iterator[T]:
        yield from self.__results

    def __getitem__(self, index: int) -> T:
        return self.__results[index]

    def __len__(self) -> int:
        return len(self.__results)

    def __repr__(self) -> str:
        return self.__results.__repr__()
