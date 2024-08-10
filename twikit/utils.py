from __future__ import annotations

import base64
import json
from datetime import datetime
from httpx import AsyncHTTPTransport
from typing import TYPE_CHECKING, Any, Awaitable, Generic, Iterator, Literal, TypedDict, TypeVar

if TYPE_CHECKING:
    from .client.client import Client

T = TypeVar('T')


class Result(Generic[T]):
    """
    This class is for storing multiple results.
    The `next` method can be used to retrieve further results.
    As with a regular list, you can access elements by
    specifying indexes and iterate over elements using a for loop.

    Attributes
    ----------
    next_cursor : :class:`str`
        Cursor used to obtain the next result.
    previous_cursor : :class:`str`
        Cursor used to obtain the previous result.
    token : :class:`str`
        Alias of `next_cursor`.
    cursor : :class:`str`
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

    @classmethod
    def empty(cls):
        return cls([])

    def __iter__(self) -> Iterator[T]:
        yield from self.__results

    def __getitem__(self, index: int) -> T:
        return self.__results[index]

    def __len__(self) -> int:
        return len(self.__results)

    def __repr__(self) -> str:
        return self.__results.__repr__()


class Flow:
    def __init__(self, client: Client, guest_token: str) -> None:
        self._client = client
        self.guest_token = guest_token
        self.response = None

    async def execute_task(self, *subtask_inputs, **kwargs) -> None:
        response, _ = await self._client.v11.onboarding_task(
            self.guest_token, self.token, list(subtask_inputs), **kwargs
        )
        self.response = response

    async def sso_init(self, provider: str) -> None:
        await self._client.v11.sso_init(provider, self.guest_token)

    @property
    def token(self) -> str | None:
        if self.response is None:
            return None
        return self.response.get('flow_token')

    @property
    def task_id(self) -> str | None:
        if self.response is None:
            return None
        if len(self.response['subtasks']) <= 0:
            return None
        return self.response['subtasks'][0]['subtask_id']


def find_dict(obj: list | dict, key: str | int, find_one: bool = False) -> list[Any]:
    """
    Retrieves elements from a nested dictionary.
    """
    results = []
    if isinstance(obj, dict):
        if key in obj:
            results.append(obj.get(key))
            if find_one:
                return results
    if isinstance(obj, (list, dict)):
        for elem in (obj if isinstance(obj, list) else obj.values()):
            r = find_dict(elem, key, find_one)
            results += r
            if r and find_one:
                return results
    return results


def httpx_transport_to_url(transport: AsyncHTTPTransport) -> str:
    url = transport._pool._proxy_url
    scheme = url.scheme.decode()
    host = url.host.decode()
    port = url.port
    auth = None
    if transport._pool._proxy_headers:
        auth_header = dict(transport._pool._proxy_headers)[b'Proxy-Authorization'].decode()
        auth = base64.b64decode(auth_header.split()[1]).decode()

    url_str = f'{scheme}://'
    if auth is not None:
        url_str += auth + '@'
    url_str += host
    if port is not None:
        url_str += f':{port}'
    return url_str


def get_query_id(url: str) -> str:
    """
    Extracts the identifier from a URL.

    Examples
    --------
    >>> get_query_id('https://twitter.com/i/api/graphql/queryid/...')
    'queryid'
    """
    return url.rsplit('/', 2)[-2]


def timestamp_to_datetime(timestamp: str) -> datetime:
    return datetime.strptime(timestamp, '%a %b %d %H:%M:%S %z %Y')


def build_tweet_data(raw_data: dict) -> dict:
    return {
        **raw_data,
        'rest_id': raw_data['id'],
        'is_translatable': None,
        'views': {},
        'edit_control': {},
        'legacy': {
            'created_at': raw_data.get('created_at'),
            'full_text': raw_data.get('full_text') or raw_data.get('text'),
            'lang': raw_data.get('lang'),
            'is_quote_status': raw_data.get('is_quote_status'),
            'in_reply_to_status_id_str': raw_data.get('in_reply_to_status_id_str'),
            'retweeted_status_result': raw_data.get('retweeted_status_result'),
            'possibly_sensitive': raw_data.get('possibly_sensitive'),
            'possibly_sensitive_editable': raw_data.get('possibly_sensitive_editable'),
            'quote_count': raw_data.get('quote_count'),
            'entities': raw_data.get('entities'),
            'reply_count': raw_data.get('reply_count'),
            'favorite_count': raw_data.get('favorite_count'),
            'favorited': raw_data.get('favorited'),
            'retweet_count': raw_data.get('retweet_count')
        }
    }


def build_user_data(raw_data: dict) -> dict:
    return {
        **raw_data,
        'rest_id': raw_data['id'],
        'is_blue_verified': raw_data.get('ext_is_blue_verified'),
        'legacy': {
            'created_at': raw_data.get('created_at'),
            'name': raw_data.get('name'),
            'screen_name': raw_data.get('screen_name'),
            'profile_image_url_https': raw_data.get('profile_image_url_https'),
            'location': raw_data.get('location'),
            'description': raw_data.get('description'),
            'entities': raw_data.get('entities'),
            'pinned_tweet_ids_str': raw_data.get('pinned_tweet_ids_str'),
            'verified': raw_data.get('verified'),
            'possibly_sensitive': raw_data.get('possibly_sensitive'),
            'can_dm': raw_data.get('can_dm'),
            'can_media_tag': raw_data.get('can_media_tag'),
            'want_retweets': raw_data.get('want_retweets'),
            'default_profile': raw_data.get('default_profile'),
            'default_profile_image': raw_data.get('default_profile_image'),
            'has_custom_timelines': raw_data.get('has_custom_timelines'),
            'followers_count': raw_data.get('followers_count'),
            'fast_followers_count': raw_data.get('fast_followers_count'),
            'normal_followers_count': raw_data.get('normal_followers_count'),
            'friends_count': raw_data.get('friends_count'),
            'favourites_count': raw_data.get('favourites_count'),
            'listed_count': raw_data.get('listed_count'),
            'media_count': raw_data.get('media_count'),
            'statuses_count': raw_data.get('statuses_count'),
            'is_translator': raw_data.get('is_translator'),
            'translator_type': raw_data.get('translator_type'),
            'withheld_in_countries': raw_data.get('withheld_in_countries'),
            'url': raw_data.get('url'),
            'profile_banner_url': raw_data.get('profile_banner_url')
        }
    }


def flatten_params(params: dict) -> dict:
    flattened_params = {}
    for key, value in params.items():
        if isinstance(value, (list, dict)):
            value = json.dumps(value)
        flattened_params[key] = value
    return flattened_params


def b64_to_str(b64: str) -> str:
    return base64.b64decode(b64).decode()


def find_entry_by_type(entries, type_filter):
    for entry in entries:
        if entry.get('type') == type_filter:
            return entry
    return None


FILTERS = Literal[
    'media',
    'retweets',
    'native_video',
    'periscope',
    'vine',
    'images',
    'twimg',
    'links'
]


class SearchOptions(TypedDict):
    exact_phrases: list[str]
    or_keywords: list[str]
    exclude_keywords: list[str]
    hashtags: list[str]
    from_user: str
    to_user: str
    mentioned_users: list[str]
    filters: list[FILTERS]
    exclude_filters: list[FILTERS]
    urls: list[str]
    since: str
    until: str
    positive: bool
    negative: bool
    question: bool


def build_query(text: str, options: SearchOptions) -> str:
    """
    Builds a search query based on the given text and search options.

    Parameters
    ----------
    text : str
        The base text of the search query.
    options : SearchOptions
        A dictionary containing various search options.
        - exact_phrases: list[str]
            List of exact phrases to include in the search query.
        - or_keywords: list[str]
            List of keywords where tweets must contain at least
            one of these keywords.
        - exclude_keywords: list[str]
            A list of keywords that the tweet must contain these keywords.
        - hashtags: list[str]
            List of hashtags to include in the search query.
        - from_user: str
            Specify a username. Only tweets from this user will
            be includedin the search.
        - to_user: str
            Specify a username. Only tweets sent to this user will
            be included in the search.
        - mentioned_users: list[str]
            List of usernames. Only tweets mentioning these users will
            be included in the search.
        - filters: list[FILTERS]
            List of tweet filters to include in the search query.
        - exclude_filters: list[FILTERS]
            List of tweet filters to exclude from the search query.
        - urls: list[str]
            List of URLs. Only tweets containing these URLs will be
            included in the search.
        - since: str
            Specify a date (formatted as 'YYYY-MM-DD'). Only tweets since
            this date will be included in the search.
        - until: str
            Specify a date (formatted as 'YYYY-MM-DD'). Only tweets until
            this date will be included in the search.
        - positive: bool
            Include positive sentiment in the search.
        - negative: bool
            Include negative sentiment in the search.
        - question: bool
            Search for tweets in questionable form.

        https://developer.twitter.com/en/docs/twitter-api/v1/rules-and-filtering/search-operators

    Returns
    -------
    str
        The constructed Twitter search query.
    """
    if exact_phrases := options.get('exact_phrases'):
        text += ' ' + ' '.join(
            [f'"{i}"' for i in exact_phrases]
        )

    if or_keywords := options.get('or_keywords'):
        text += ' ' + ' OR '.join(or_keywords)

    if exclude_keywords := options.get('exclude_keywords'):
        text += ' ' + ' '.join(
            [f'-"{i}"' for i in exclude_keywords]
        )

    if hashtags := options.get('hashtags'):
        text += ' ' + ' '.join(
            [f'#{i}' for i in hashtags]
        )

    if from_user := options.get('from_user'):
        text +=f' from:{from_user}'

    if to_user := options.get('to_user'):
        text += f' to:{to_user}'

    if mentioned_users := options.get('mentioned_users'):
        text += ' ' + ' '.join(
            [f'@{i}' for i in mentioned_users]
        )

    if filters := options.get('filters'):
        text += ' ' + ' '.join(
            [f'filter:{i}' for i in filters]
        )

    if exclude_filters := options.get('exclude_filters'):
        text += ' ' + ' '.join(
            [f'-filter:{i}' for i in exclude_filters]
        )

    if urls := options.get('urls'):
        text += ' ' + ' '.join(
            [f'url:{i}' for i in urls]
        )

    if since := options.get('since'):
        text += f' since:{since}'

    if until := options.get('until'):
        text += f' until:{until}'

    if options.get('positive') is True:
        text += ' :)'

    if options.get('negative') is True:
        text += ' :('

    if options.get('question') is True:
        text += ' ?'

    return text
