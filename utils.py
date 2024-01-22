from __future__ import annotations

from typing import Callable, Generic, Iterator, TypeVar

TOKEN = 'AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'


class Endpoint:
    TASK = "https://api.twitter.com/1.1/onboarding/task.json"
    LOGOUT = "https://api.twitter.com/1.1/account/logout.json"
    CREATE_TWEET = 'https://twitter.com/i/api/graphql/SiM_cAu83R0wnrpmKQQSEw/CreateTweet'
    SEARCH_TIMELINE = 'https://twitter.com/i/api/graphql/HgiQ8U_E6g-HE_I6Pp_2UA/SearchTimeline'
    UPLOAD_MEDIA = 'https://upload.twitter.com/i/media/upload.json'
    GET_GUEST_TOKEN = 'https://api.twitter.com/1.1/guest/activate.json'

T = TypeVar('T')


class Result(Generic[T]):
    def __init__(
        self,
        results: list[T],
        fetch_next_result: Callable = None,
        cursor: str = None
    ) -> None:
        self.__results = results
        self.cursor = cursor
        self.__fetch_next_result = fetch_next_result

    @property
    def next(self) -> Result[T]:
        return self.__fetch_next_result()

    def __iter__(self) -> Iterator[T]:
        yield from self.__results

    def __getitem__(self, index: int) -> T:
        return self.__results[index]

    def __repr__(self) -> str:
        return self.__results.__repr__()
