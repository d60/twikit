from __future__ import annotations

from typing import Awaitable, Generic, Iterator, TypeVar

T = TypeVar('T')


class Result(Generic[T]):
    """
    This class is for storing multiple results.
    The `next` method can be used to retrieve further results.
    As with a regular list, you can access elements by
    specifying indexes and iterate over elements using a for loop.

    Attributes
    ----------
    next_cursor : str
        Cursor used to obtain the next result.
    previous_cursor : str
        Cursor used to obtain the previous result.
    token : str
        Alias of `next_cursor`.
    cursor : str
        Alias of `next_cursor`.
    """

    def __init__(
        self,
        results: list[T],
        fetch_next_result: Awaitable | None = None,
        next_cursor: str | None = None,
        fetch_previous_result: Awaitable | None = None,
        previous_cursor: str | None = None
    ) -> None:
        self.__results = results
        self.next_cursor = next_cursor
        self.__fetch_next_result = fetch_next_result
        self.previous_cursor = previous_cursor
        self.__fetch_previous_result = fetch_previous_result

    async def next(self) -> Result[T]:
        """
        The next result.
        """
        if self.__fetch_next_result is None:
            return Result([])
        return await self.__fetch_next_result()

    async def previous(self) -> Result[T]:
        """
        The previous result.
        """
        if self.__fetch_previous_result is None:
            return Result([])
        return await self.__fetch_previous_result()

    @property
    def cursor(self) -> str:
        """Alias of `next_token`
        """
        return self.next_cursor

    @property
    def token(self) -> str:
        """Alias of `next_token`
        """
        return self.next_cursor

    def __iter__(self) -> Iterator[T]:
        yield from self.__results

    def __getitem__(self, index: int) -> T:
        return self.__results[index]

    def __len__(self) -> int:
        return len(self.__results)

    def __repr__(self) -> str:
        return self.__results.__repr__()
