from __future__ import annotations

import json
import warnings
from functools import partial
from typing import Any, Literal

from httpx import AsyncClient, AsyncHTTPTransport, Response
from httpx._utils import URLPattern

from ..client.gql import GQLClient
from ..client.v11 import V11Client
from ..constants import TOKEN
from ..errors import (
    BadRequest,
    Forbidden,
    NotFound,
    RequestTimeout,
    ServerError,
    TooManyRequests,
    TwitterException,
    Unauthorized
)
from ..utils import Result, find_dict, find_entry_by_type, httpx_transport_to_url
from .tweet import Tweet
from .user import User


def tweet_from_data(client: GuestClient, data: dict) -> Tweet:
    ':meta private:'
    tweet_data_ = find_dict(data, 'result', True)
    if not tweet_data_:
        return None
    tweet_data = tweet_data_[0]

    if tweet_data.get('__typename') == 'TweetTombstone':
        return None
    if 'tweet' in tweet_data:
        tweet_data = tweet_data['tweet']
    if 'core' not in tweet_data:
        return None
    if 'result' not in tweet_data['core']['user_results']:
        return None
    if 'legacy' not in tweet_data:
        return None

    user_data = tweet_data['core']['user_results']['result']
    return Tweet(client, tweet_data, User(client, user_data))



class GuestClient:
    """
    A client for interacting with the Twitter API as a guest.
    This class is used for interacting with the Twitter API
    without requiring authentication.

    Parameters
    ----------
    language : :class:`str` | None, default=None
        The language code to use in API requests.
    proxy : :class:`str` | None, default=None
        The proxy server URL to use for request
        (e.g., 'http://0.0.0.0:0000').

    Examples
    --------
    >>> client = GuestClient()
    >>> await client.activate()  # Activate the client by generating a guest token.
    """

    def __init__(
        self,
        language: str | None = None,
        proxy: str | None = None,
        **kwargs
    ) -> None:
        if 'proxies' in kwargs:
            message = (
                "The 'proxies' argument is now deprecated. Use 'proxy' "
                "instead. https://github.com/encode/httpx/pull/2879"
            )
            warnings.warn(message)

        self.http = AsyncClient(proxy=proxy, **kwargs)
        self.language = language
        self.proxy = proxy

        self._token = TOKEN
        self._user_agent = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                            'AppleWebKit/537.36 (KHTML, like Gecko) '
                            'Chrome/122.0.0.0 Safari/537.36')
        self._guest_token: str | None = None  # set when activate method is called
        self.gql = GQLClient(self)
        self.v11 = V11Client(self)

    async def request(
        self,
        method: str,
        url: str,
        raise_exception: bool = True,
        **kwargs
    ) -> tuple[dict | Any, Response]:
        ':meta private:'
        response = await self.http.request(method, url, **kwargs)

        try:
            response_data = response.json()
        except json.decoder.JSONDecodeError:
            response_data = response.text

        status_code = response.status_code

        if status_code >= 400 and raise_exception:
            message = f'status: {status_code}, message: "{response.text}"'
            if status_code == 400:
                raise BadRequest(message, headers=response.headers)
            elif status_code == 401:
                raise Unauthorized(message, headers=response.headers)
            elif status_code == 403:
                raise Forbidden(message, headers=response.headers)
            elif status_code == 404:
                raise NotFound(message, headers=response.headers)
            elif status_code == 408:
                raise RequestTimeout(message, headers=response.headers)
            elif status_code == 429:
                raise TooManyRequests(message, headers=response.headers)
            elif 500 <= status_code < 600:
                raise ServerError(message, headers=response.headers)
            else:
                raise TwitterException(message, headers=response.headers)

        return response_data, response

    async def get(self, url, **kwargs) -> tuple[dict | Any, Response]:
        ':meta private:'
        return await self.request('GET', url, **kwargs)

    async def post(self, url, **kwargs) -> tuple[dict | Any, Response]:
        ':meta private:'
        return await self.request('POST', url, **kwargs)

    @property
    def proxy(self) -> str:
        ':meta private:'
        transport: AsyncHTTPTransport = self.http._mounts.get(
            URLPattern('all://')
        )
        if transport is None:
            return None
        if not hasattr(transport._pool, '_proxy_url'):
            return None
        return httpx_transport_to_url(transport)

    @proxy.setter
    def proxy(self, url: str) -> None:
        self.http._mounts = {
            URLPattern('all://'): AsyncHTTPTransport(proxy=url)
        }

    @property
    def _base_headers(self) -> dict[str, str]:
        """
        Base headers for Twitter API requests.
        """
        headers = {
            'authorization': f'Bearer {self._token}',
            'content-type': 'application/json',
            'X-Twitter-Active-User': 'yes',
            'Referer': 'https://twitter.com/',
        }

        if self.language is not None:
            headers['Accept-Language'] = self.language
            headers['X-Twitter-Client-Language'] = self.language

        if self._guest_token is not None:
            headers['X-Guest-Token'] = self._guest_token

        return headers

    async def activate(self) -> str:
        """
        Activate the client by generating a guest token.
        """
        response, _ = await self.v11.guest_activate()
        self._guest_token = response['guest_token']
        return self._guest_token

    async def get_user_by_screen_name(self, screen_name: str) -> User:
        """
        Retrieves a user object based on the provided screen name.

        Parameters
        ----------
        screen_name : :class:`str`
            The screen name of the user to retrieve.

        Returns
        -------
        :class:`.user.User`
            An instance of the `User` class containing user details.

        Examples
        --------
        >>> user = await client.get_user_by_screen_name('example_user')
        >>> print(user)
        <User id="...">
        """
        response, _ = await self.gql.user_by_screen_name(screen_name)
        return User(self, response['data']['user']['result'])

    async def get_user_by_id(self, user_id: str) -> User:
        """
        Retrieves a user object based on the provided user ID.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user to retrieve.

        Returns
        -------
        :class:`.user.User`
            An instance of the `User` class

        Examples
        --------
        >>> user = await client.get_user_by_id('123456789')
        >>> print(user)
        <User id="123456789">
        """
        response, _ = await self.gql.user_by_rest_id(user_id)
        return User(self, response['data']['user']['result'])

    async def get_user_tweets(
        self,
        user_id: str,
        tweet_type: Literal['Tweets'] = 'Tweets',
        count: int = 40,
    ) -> list[Tweet]:
        """
        Fetches tweets from a specific user's timeline.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the Twitter user whose tweets to retrieve.
            To get the user id from the screen name, you can use
            `get_user_by_screen_name` method.
        tweet_type : {'Tweets'}, default='Tweets'
            The type of tweets to retrieve.
        count : :class:`int`, default=40
            The number of tweets to retrieve.

        Returns
        -------
        list[:class:`.tweet.Tweet`]
            A Result object containing a list of `Tweet` objects.

        Examples
        --------
        >>> user_id = '...'

        If you only have the screen name, you can get the user id as follows:

        >>> screen_name = 'example_user'
        >>> user = client.get_user_by_screen_name(screen_name)
        >>> user_id = user.id

        >>> tweets = await client.get_user_tweets(user_id)
        >>> for tweet in tweets:
        ...    print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...

        See Also
        --------
        .get_user_by_screen_name
        """
        tweet_type = tweet_type.capitalize()
        f = {
            'Tweets': self.gql.user_tweets,
        }[tweet_type]
        response, _ = await f(user_id, count, None)
        instructions_ = find_dict(response, 'instructions', True)
        if not instructions_:
            return []
        instructions = instructions_[0]
        items = find_entry_by_type(instructions, 'TimelineAddEntries')['entries']
        results = []

        for item in items:
            entry_id = item['entryId']
            if not entry_id.startswith(('tweet', 'profile-conversation', 'profile-grid')):
                continue
            tweet = tweet_from_data(self, item)
            if tweet is None:
                continue
            results.append(tweet)

        return results

    async def get_tweet_by_id(self, tweet_id: str) -> Tweet:
        """
        Fetches a tweet by tweet ID.

        Parameters
        ----------
        tweet_id : :class:`str`
            The ID of the tweet.

        Returns
        -------
        :class:`.tweet.Tweet`
            Tweet object

        Examples
        --------
        >>> await client.get_tweet_by_id('123456789')
        <Tweet id="123456789">
        """
        response, _ = await self.gql.tweet_result_by_rest_id(tweet_id)
        return tweet_from_data(self, response)

    async def get_user_highlights_tweets(
        self,
        user_id: str,
        count: int = 20,
        cursor: str | None = None
    ) -> Result[Tweet]:
        """
        Retrieves highlighted tweets from a user's timeline.

        Parameters
        ----------
        user_id : :class:`str`
            The user ID
        count : :class:`int`, default=20
            The number of tweets to retrieve.

        Returns
        -------
        Result[:class:`.tweet.Tweet`]
            An instance of the `Result` class containing the highlighted tweets.

        Examples
        --------
        >>> result = await client.get_user_highlights_tweets('123456789')
        >>> for tweet in result:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...

        >>> more_results = await result.next()  # Retrieve more highlighted tweets
        >>> for tweet in more_results:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...
        """
        response, _ = await self.gql.user_highlights_tweets(user_id, count, cursor)

        instructions = response['data']['user']['result']['timeline']['timeline']['instructions']
        instruction = find_entry_by_type(instructions, 'TimelineAddEntries')
        if instruction is None:
            return Result.empty()
        entries = instruction['entries']
        previous_cursor = None
        next_cursor = None
        results = []

        for entry in entries:
            entryId = entry['entryId']
            if entryId.startswith('tweet'):
                results.append(tweet_from_data(self, entry))
            elif entryId.startswith('cursor-top'):
                previous_cursor = entry['content']['value']
            elif entryId.startswith('cursor-bottom'):
                next_cursor = entry['content']['value']

        return Result(
            results,
            partial(self.get_user_highlights_tweets, user_id, count, next_cursor),
            next_cursor,
            partial(self.get_user_highlights_tweets, user_id, count, previous_cursor),
            previous_cursor
        )
