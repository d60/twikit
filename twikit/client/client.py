from __future__ import annotations

import asyncio
import io
import json
import re
import warnings
from functools import partial
from typing import Any, AsyncGenerator, Literal

import filetype
import pyotp
from httpx import AsyncClient, AsyncHTTPTransport, Response
from httpx._utils import URLPattern

from .._captcha import Capsolver
from ..bookmark import BookmarkFolder
from ..community import Community, CommunityMember
from ..constants import TOKEN
from ..errors import (
    AccountLocked,
    AccountSuspended,
    BadRequest,
    CouldNotTweet,
    Forbidden,
    InvalidMedia,
    NotFound,
    RequestTimeout,
    ServerError,
    TooManyRequests,
    TweetNotAvailable,
    TwitterException,
    Unauthorized,
    UserNotFound,
    UserUnavailable,
    raise_exceptions_from_response
)
from ..geo import Place, _places_from_response
from ..group import Group, GroupMessage
from ..list import List
from ..message import Message
from ..notification import Notification
from ..streaming import Payload, StreamingSession, _payload_from_data
from ..trend import Location, PlaceTrend, PlaceTrends, Trend
from ..tweet import CommunityNote, Poll, ScheduledTweet, Tweet, tweet_from_data
from ..user import User
from ..utils import (
    Flow,
    Result,
    build_tweet_data,
    build_user_data,
    find_dict,
    find_entry_by_type,
    httpx_transport_to_url
)
from .gql import GQLClient
from .v11 import V11Client


class Client:
    """
    A client for interacting with the Twitter API.
    Since this class is for asynchronous use,
    methods must be executed using await.

    Parameters
    ----------
    language : :class:`str` | None, default=None
        The language code to use in API requests.
    proxy : :class:`str` | None, default=None
        The proxy server URL to use for request
        (e.g., 'http://0.0.0.0:0000').
    captcha_solver : :class:`.Capsolver` | None, default=None
        See :class:`.Capsolver`.

    Examples
    --------
    >>> client = Client(language='en-US')

    >>> await client.login(
    ...     auth_info_1='example_user',
    ...     auth_info_2='email@example.com',
    ...     password='00000000'
    ... )
    """

    def __init__(
        self,
        language: str | None = None,
        proxy: str | None = None,
        captcha_solver: Capsolver | None = None,
        user_agent: str | None = None,
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
        self.captcha_solver = captcha_solver
        if captcha_solver is not None:
            captcha_solver.client = self

        self._token = TOKEN
        self._user_id = None
        self._user_agent = user_agent or 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15'
        self._act_as = None

        self.gql = GQLClient(self)
        self.v11 = V11Client(self)

    async def request(
        self,
        method: str,
        url: str,
        auto_unlock: bool = True,
        raise_exception: bool = True,
        **kwargs
    ) -> tuple[dict | Any, Response]:
        ':meta private:'
        cookies_backup = self.get_cookies().copy()
        response = await self.http.request(method, url, **kwargs)
        self._remove_duplicate_ct0_cookie()

        try:
            response_data = response.json()
        except json.decoder.JSONDecodeError:
            response_data = response.text

        if isinstance(response_data, dict) and 'errors' in response_data:
            error_code = response_data['errors'][0]['code']
            error_message = response_data['errors'][0].get('message')
            if error_code in (37, 64):
                # Account suspended
                raise AccountSuspended(error_message)

            if error_code == 326:
                # Account unlocking
                if self.captcha_solver is None:
                    raise AccountLocked(
                        'Your account is locked. Visit '
                        'https://twitter.com/account/access to unlock it.'
                    )
                if auto_unlock:
                    await self.unlock()
                    self.set_cookies(cookies_backup, clear_cookies=True)
                    response = await self.http.request(method, url, **kwargs)
                    self._remove_duplicate_ct0_cookie()
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
                if await self._get_user_state() == 'suspended':
                    raise AccountSuspended(message, headers=response.headers)
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

    def _remove_duplicate_ct0_cookie(self) -> None:
        cookies = {}
        for cookie in self.http.cookies.jar:
            if 'ct0' in cookies and cookie.name == 'ct0':
                continue
            cookies[cookie.name] = cookie.value
        self.http.cookies = list(cookies.items())

    @property
    def proxy(self) -> str:
        ':meta private:'
        transport: AsyncHTTPTransport = self.http._mounts.get(URLPattern('all://'))
        if transport is None:
            return None
        if not hasattr(transport._pool, '_proxy_url'):
            return None
        return httpx_transport_to_url(transport)

    @proxy.setter
    def proxy(self, url: str) -> None:
        self.http._mounts = {URLPattern('all://'): AsyncHTTPTransport(proxy=url)}

    def _get_csrf_token(self) -> str:
        """
        Retrieves the Cross-Site Request Forgery (CSRF) token from the
        current session's cookies.

        Returns
        -------
        :class:`str`
            The CSRF token as a string.
        """
        return self.http.cookies.get('ct0')

    @property
    def _base_headers(self) -> dict[str, str]:
        """
        Base headers for Twitter API requests.
        """
        headers = {
            'authorization': f'Bearer {self._token}',
            'content-type': 'application/json',
            'X-Twitter-Auth-Type': 'OAuth2Session',
            'X-Twitter-Active-User': 'yes',
            'Referer': 'https://twitter.com/',
            'User-Agent': self._user_agent,
        }

        if self.language is not None:
            headers['Accept-Language'] = self.language
            headers['X-Twitter-Client-Language'] = self.language

        csrf_token = self._get_csrf_token()
        if csrf_token is not None:
            headers['X-Csrf-Token'] = csrf_token
        if self._act_as is not None:
            headers['X-Act-As-User-Id'] = self._act_as
        return headers

    async def _get_guest_token(self) -> str:
        response, _ = await self.v11.guest_activate()
        guest_token = response['guest_token']
        return guest_token

    async def _ui_metrix(self) -> str:
        js, _ = await self.get('https://twitter.com/i/js_inst?c_name=ui_metrics')
        return re.findall(r'return ({.*?});', js, re.DOTALL)[0]

    async def login(
        self,
        *,
        auth_info_1: str,
        auth_info_2: str | None = None,
        password: str,
        totp_secret: str | None = None
    ) -> dict:
        """
        Logs into the account using the specified login information.
        `auth_info_1` and `password` are required parameters.
        `auth_info_2` is optional and can be omitted, but it is
        recommended to provide if available.
        The order in which you specify authentication information
        (auth_info_1 and auth_info_2) is flexible.

        Parameters
        ----------
        auth_info_1 : :class:`str`
            The first piece of authentication information,
            which can be a username, email address, or phone number.
        auth_info_2 : :class:`str`, default=None
            The second piece of authentication information,
            which is optional but recommended to provide.
            It can be a username, email address, or phone number.
        password : :class:`str`
            The password associated with the account.
        totp_secret : :class:`str`
            The TOTP (Time-Based One-Time Password) secret key used for
            two-factor authentication (2FA).

        Examples
        --------
        >>> await client.login(
        ...     auth_info_1='example_user',
        ...     auth_info_2='email@example.com',
        ...     password='00000000'
        ... )
        """
        self.http.cookies.clear()
        guest_token = await self._get_guest_token()

        flow = Flow(self, guest_token)

        await flow.execute_task(params={'flow_name': 'login'}, data={
            'input_flow_data': {
                'flow_context': {
                    'debug_overrides': {},
                    'start_location': {
                        'location': 'splash_screen'
                    }
                }
            },
            'subtask_versions': {
                'action_list': 2,
                'alert_dialog': 1,
                'app_download_cta': 1,
                'check_logged_in_account': 1,
                'choice_selection': 3,
                'contacts_live_sync_permission_prompt': 0,
                'cta': 7,
                'email_verification': 2,
                'end_flow': 1,
                'enter_date': 1,
                'enter_email': 2,
                'enter_password': 5,
                'enter_phone': 2,
                'enter_recaptcha': 1,
                'enter_text': 5,
                'enter_username': 2,
                'generic_urt': 3,
                'in_app_notification': 1,
                'interest_picker': 3,
                'js_instrumentation': 1,
                'menu_dialog': 1,
                'notifications_permission_prompt': 2,
                'open_account': 2,
                'open_home_timeline': 1,
                'open_link': 1,
                'phone_verification': 4,
                'privacy_options': 1,
                'security_key': 3,
                'select_avatar': 4,
                'select_banner': 2,
                'settings_list': 7,
                'show_code': 1,
                'sign_up': 2,
                'sign_up_review': 4,
                'tweet_selection_urt': 1,
                'update_users': 1,
                'upload_media': 1,
                'user_recommendations_list': 4,
                'user_recommendations_urt': 1,
                'wait_spinner': 3,
                'web_modal': 1
            }
        })
        await flow.sso_init('apple')
        await flow.execute_task({
            "subtask_id": "LoginJsInstrumentationSubtask",
            "js_instrumentation": {
                "response": await self._ui_metrix(),
                "link": "next_link"
            }
        })
        await flow.execute_task({
            'subtask_id': 'LoginEnterUserIdentifierSSO',
            'settings_list': {
                'setting_responses': [
                    {
                        'key': 'user_identifier',
                        'response_data': {
                            'text_data': {'result': auth_info_1}
                        }
                    }
                ],
                'link': 'next_link'
            }
        })

        if flow.task_id == 'LoginEnterAlternateIdentifierSubtask':
            await flow.execute_task({
                'subtask_id': 'LoginEnterAlternateIdentifierSubtask',
                'enter_text': {
                    'text': auth_info_2,
                    'link': 'next_link'
                }
            })

        await flow.execute_task({
            'subtask_id': 'LoginEnterPassword',
            'enter_password': {
                'password': password,
                'link': 'next_link'
            }
        })

        if flow.task_id == 'DenyLoginSubtask':
            raise TwitterException(flow.response['subtasks'][0]['cta']['secondary_text']['text'])

        await flow.execute_task({
            'subtask_id': 'AccountDuplicationCheck',
            'check_logged_in_account': {
                'link': 'AccountDuplicationCheck_false'
            }
        })

        if not flow.response['subtasks']:
            return

        self._user_id = find_dict(flow.response, 'id_str', find_one=True)[0]

        if flow.task_id == 'LoginTwoFactorAuthChallenge':
            if totp_secret is None:
                print(find_dict(flow.response, 'secondary_text', find_one=True)[0]['text'])
                totp_code = input('>>>')
            else:
                totp_code = pyotp.TOTP(totp_secret).now()

            await flow.execute_task({
                'subtask_id': 'LoginTwoFactorAuthChallenge',
                'enter_text': {
                    'text': totp_code,
                    'link': 'next_link'
                }
            })

        if flow.task_id == 'LoginAcid':
            print(find_dict(flow.response, 'secondary_text', find_one=True)[0]['text'])

            await flow.execute_task({
                'subtask_id': 'LoginAcid',
                'enter_text': {
                    'text': input('>>> '),
                    'link': 'next_link'
                }
            })

        return flow.response

    async def logout(self) -> Response:
        """
        Logs out of the currently logged-in account.
        """
        response, _ = await self.v11.account_logout()
        return response

    async def unlock(self) -> None:
        """
        Unlocks the account using the provided CAPTCHA solver.

        See Also
        --------
        .capsolver
        """
        if self.captcha_solver is None:
            raise ValueError('Captcha solver is not provided.')

        response, html = await self.captcha_solver.get_unlock_html()

        if html.delete_button:
            response, html = await self.captcha_solver.confirm_unlock(
                html.authenticity_token,
                html.assignment_token,
                ui_metrics=True
            )

        if html.start_button or html.finish_button:
            response, html = await self.captcha_solver.confirm_unlock(
                html.authenticity_token,
                html.assignment_token,
                ui_metrics=True
            )

        cookies_backup = self.get_cookies().copy()
        max_unlock_attempts = self.captcha_solver.max_attempts
        attempt = 0
        while attempt < max_unlock_attempts:
            attempt += 1

            if html.authenticity_token is None:
                response, html = await self.captcha_solver.get_unlock_html()

            result = self.captcha_solver.solve_funcaptcha(html.blob)
            if result['errorId'] == 1:
                continue

            self.set_cookies(cookies_backup, clear_cookies=True)
            response, html = await self.captcha_solver.confirm_unlock(
                html.authenticity_token,
                html.assignment_token,
                result['solution']['token'],
            )

            if html.finish_button:
                response, html = await self.captcha_solver.confirm_unlock(
                    html.authenticity_token,
                    html.assignment_token,
                    ui_metrics=True
                )
            finished = (
                response.next_request is not None and
                response.next_request.url.path == '/'
            )
            if finished:
                return
        raise Exception('could not unlock the account.')

    def get_cookies(self) -> dict:
        """
        Get the cookies.
        You can skip the login procedure by loading the saved cookies
        using the :func:`set_cookies` method.

        Examples
        --------
        >>> client.get_cookies()

        See Also
        --------
        .set_cookies
        .load_cookies
        .save_cookies
        """
        return dict(self.http.cookies)

    def save_cookies(self, path: str) -> None:
        """
        Save cookies to file in json format.
        You can skip the login procedure by loading the saved cookies
        using the :func:`load_cookies` method.

        Parameters
        ----------
        path : :class:`str`
            The path to the file where the cookie will be stored.

        Examples
        --------
        >>> client.save_cookies('cookies.json')

        See Also
        --------
        .load_cookies
        .get_cookies
        .set_cookies
        """
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.get_cookies(), f)

    def set_cookies(self, cookies: dict, clear_cookies: bool = False) -> None:
        """
        Sets cookies.
        You can skip the login procedure by loading a saved cookies.

        Parameters
        ----------
        cookies : :class:`dict`
            The cookies to be set as key value pair.

        Examples
        --------
        >>> with open('cookies.json', 'r', encoding='utf-8') as f:
        ...     client.set_cookies(json.load(f))

        See Also
        --------
        .get_cookies
        .load_cookies
        .save_cookies
        """
        if clear_cookies:
            self.http.cookies.clear()
        self.http.cookies.update(cookies)

    def load_cookies(self, path: str) -> None:
        """
        Loads cookies from a file.
        You can skip the login procedure by loading a saved cookies.

        Parameters
        ----------
        path : :class:`str`
            Path to the file where the cookie is stored.

        Examples
        --------
        >>> client.load_cookies('cookies.json')

        See Also
        --------
        .get_cookies
        .save_cookies
        .set_cookies
        """
        with open(path, 'r', encoding='utf-8') as f:
            self.set_cookies(json.load(f))

    def set_delegate_account(self, user_id: str | None) -> None:
        """
        Sets the account to act as.

        Parameters
        ----------
        user_id : :class:`str` | None
            The user ID of the account to act as.
            Set to None to clear the delegated account.
        """
        self._act_as = user_id

    async def user_id(self) -> str:
        """
        Retrieves the user ID associated with the authenticated account.
        """
        if self._user_id is not None:
            return self._user_id
        response, _ = await self.v11.settings()
        screen_name = response['screen_name']
        self._user_id = (await self.get_user_by_screen_name(screen_name)).id
        return self._user_id

    async def user(self) -> User:
        """
        Retrieve detailed information about the authenticated user.
        """
        return await self.get_user_by_id(await self.user_id())

    async def search_tweet(
        self,
        query: str,
        product: Literal['Top', 'Latest', 'Media'],
        count: int = 20,
        cursor: str | None = None
    ) -> Result[Tweet]:
        """
        Searches for tweets based on the specified query and
        product type.

        Parameters
        ----------
        query : :class:`str`
            The search query.
        product : {'Top', 'Latest', 'Media'}
            The type of tweets to retrieve.
        count : :class:`int`, default=20
            The number of tweets to retrieve, between 1 and 20.
        cursor : :class:`str`, default=20
            Token to retrieve more tweets.

        Returns
        -------
        Result[:class:`Tweet`]
            An instance of the `Result` class containing the
            search results.

        Examples
        --------
        >>> tweets = await client.search_tweet('query', 'Top')
        >>> for tweet in tweets:
        ...    print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...

        >>> more_tweets = await tweets.next()  # Retrieve more tweets
        >>> for tweet in more_tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...

        >>> # Retrieve previous tweets
        >>> previous_tweets = await tweets.previous()
        """
        product = product.capitalize()

        response, _ = await self.gql.search_timeline(query, product, count, cursor)
        instructions = find_dict(response, 'instructions', find_one=True)
        if not instructions:
            return Result([])
        instructions = instructions[0]

        if product == 'Media' and cursor is not None:
            items = find_dict(instructions, 'moduleItems', find_one=True)[0]
        else:
            items_ = find_dict(instructions, 'entries', find_one=True)
            if items_:
                items = items_[0]
            else:
                items = []
            if product == 'Media':
                if 'items' in items[0]['content']:
                    items = items[0]['content']['items']
                else:
                    items = []

        next_cursor = None
        previous_cursor = None

        results = []
        for item in items:
            if item['entryId'].startswith('cursor-bottom'):
                next_cursor = item['content']['value']
            if item['entryId'].startswith('cursor-top'):
                previous_cursor = item['content']['value']
            if not item['entryId'].startswith(('tweet', 'search-grid')):
                continue

            tweet = tweet_from_data(self, item)
            if tweet is not None:
                results.append(tweet)

        if next_cursor is None:
            if product == 'Media':
                entries = find_dict(instructions, 'entries', find_one=True)[0]
                next_cursor = entries[-1]['content']['value']
                previous_cursor = entries[-2]['content']['value']
            else:
                next_cursor = instructions[-1]['entry']['content']['value']
                previous_cursor = instructions[-2]['entry']['content']['value']

        return Result(
            results,
            partial(self.search_tweet, query, product, count, next_cursor),
            next_cursor,
            partial(self.search_tweet, query, product, count, previous_cursor),
            previous_cursor
        )

    async def search_user(
        self,
        query: str,
        count: int = 20,
        cursor: str | None = None
    ) -> Result[User]:
        """
        Searches for users based on the provided query.

        Parameters
        ----------
        query : :class:`str`
            The search query for finding users.
        count : :class:`int`, default=20
            The number of users to retrieve in each request.
        cursor : :class:`str`, default=None
            Token to retrieve more users.

        Returns
        -------
        Result[:class:`User`]
            An instance of the `Result` class containing the
            search results.

        Examples
        --------
        >>> result = await client.search_user('query')
        >>> for user in result:
        ...     print(user)
        <User id="...">
        <User id="...">
        ...
        ...

        >>> more_results = await result.next()  # Retrieve more search results
        >>> for user in more_results:
        ...     print(user)
        <User id="...">
        <User id="...">
        ...
        ...
        """
        response, _ = await self.gql.search_timeline(query, 'People', count, cursor)
        items = find_dict(response, 'entries', find_one=True)[0]
        next_cursor = items[-1]['content']['value']

        results = []
        for item in items:
            if 'itemContent' not in item['content']:
                continue
            user_info = find_dict(item, 'result', find_one=True)[0]
            results.append(User(self, user_info))

        return Result(
            results,
            partial(self.search_user, query, count, next_cursor),
            next_cursor
        )

    async def get_similar_tweets(self, tweet_id: str) -> list[Tweet]:
        """
        Retrieves tweets similar to the specified tweet (Twitter premium only).

        Parameters
        ----------
        tweet_id : :class:`str`
            The ID of the tweet for which similar tweets are to be retrieved.

        Returns
        -------
        list[:class:`Tweet`]
            A list of Tweet objects representing tweets
            similar to the specified tweet.
        """
        response, _ = await self.gql.similar_posts(tweet_id)
        items_ = find_dict(response, 'entries', find_one=True)
        results = []
        if not items_:
            return results

        for item in items_[0]:
            if not item['entryId'].startswith('tweet'):
                continue

            tweet = tweet_from_data(self, item)
            if tweet is not None:
                results.append(tweet)

        return results

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
        Result[:class:`Tweet`]
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

    async def upload_media(
        self,
        source: str | bytes,
        wait_for_completion: bool = False,
        status_check_interval: float | None = None,
        media_type: str | None = None,
        media_category: str | None = None,
        is_long_video: bool = False
    ) -> str:
        """
        Uploads media to twitter.

        Parameters
        ----------
        source : :class:`str` | :class:`bytes`
            The source of the media to be uploaded.
            It can be either a file path or bytes of the media content.
        wait_for_completion : :class:`bool`, default=False
            Whether to wait for the completion of the media upload process.
        status_check_interval : :class:`float`, default=1.0
            The interval (in seconds) to check the status of the
            media upload process.
        media_type : :class:`str`, default=None
            The MIME type of the media.
            If not specified, it will be guessed from the source.
        media_category : :class:`str`, default=None
            The media category.
        is_long_video : :class:`bool`, default=False
            If this is True, videos longer than 2:20 can be uploaded.
            (Twitter Premium only)

        Returns
        -------
        :class:`str`
            The media ID of the uploaded media.

        Examples
        --------
        Videos, images and gifs can be uploaded.

        >>> media_id_1 = await client.upload_media(
        ...     'media1.jpg',
        ... )

        >>> media_id_2 = await client.upload_media(
        ...     'media2.mp4',
        ...     wait_for_completion=True
        ... )

        >>> media_id_3 = await client.upload_media(
        ...     'media3.gif',
        ...     wait_for_completion=True,
        ...     media_category='tweet_gif'  # media_category must be specified
        ... )
        """
        if not isinstance(wait_for_completion, bool):
            raise TypeError(
                'wait_for_completion must be bool,'
                f' not {wait_for_completion.__class__.__name__}'
            )

        if isinstance(source, str):
            # If the source is a path
            with open(source, 'rb') as file:
                binary = file.read()
        elif isinstance(source, bytes):
            # If the source is bytes
            binary = source

        if media_type is None:
            # Guess mimetype if not specified
            media_type = filetype.guess(binary).mime

        if wait_for_completion:
            if media_type == 'image/gif':
                if media_category is None:
                    raise TwitterException(
                        "`media_category` must be specified to check the "
                        "upload status of gif images ('dm_gif' or 'tweet_gif')"
                    )
            elif media_type.startswith('image'):
                # Checking the upload status of an image is impossible.
                wait_for_completion = False

        total_bytes = len(binary)

        # ============ INIT =============
        response, _ = await self.v11.upload_media_init(
            media_type, total_bytes, media_category, is_long_video
        )
        media_id = response['media_id']
        # =========== APPEND ============
        segment_index = 0
        bytes_sent = 0
        MAX_SEGMENT_SIZE = 8 * 1024 * 1024  # The maximum segment size is 8 MB
        append_tasks = []
        chunk_streams: list[io.BytesIO] = []

        while bytes_sent < total_bytes:
            chunk = binary[bytes_sent:bytes_sent + MAX_SEGMENT_SIZE]
            chunk_stream = io.BytesIO(chunk)
            coro = self.v11.upload_media_append(is_long_video, media_id, segment_index, chunk_stream)
            append_tasks.append(asyncio.create_task(coro))
            chunk_streams.append(chunk_stream)

            segment_index += 1
            bytes_sent += len(chunk)

        append_gather = asyncio.gather(*append_tasks)
        await append_gather

        # Close chunk streams
        for chunk_stream in chunk_streams:
            chunk_stream.close()

        # ========== FINALIZE ===========
        await self.v11.upload_media_finelize(is_long_video, media_id)
        # ===============================

        if wait_for_completion:
            while True:
                state = await self.check_media_status(media_id, is_long_video)
                processing_info = state['processing_info']
                if 'error' in processing_info:
                    raise InvalidMedia(processing_info['error'].get('message'))
                if processing_info['state'] == 'succeeded':
                    break
                await asyncio.sleep(status_check_interval or processing_info['check_after_secs'])

        return media_id

    async def check_media_status(
        self, media_id: str, is_long_video: bool = False
    ) -> dict:
        """
        Check the status of uploaded media.

        Parameters
        ----------
        media_id : :class:`str`
            The media ID of the uploaded media.

        Returns
        -------
        dict
            A dictionary containing information about the status of
            the uploaded media.
        """
        response, _ = await self.v11.upload_media_status(is_long_video, media_id)
        return response

    async def create_media_metadata(
        self,
        media_id: str,
        alt_text: str | None = None,
        sensitive_warning: list[Literal['adult_content', 'graphic_violence', 'other']] = None
    ) -> Response:
        """
        Adds metadata to uploaded media.

        Parameters
        ----------
        media_id : :class:`str`
            The media id for which to create metadata.
        alt_text : :class:`str` | None, default=None
            Alternative text for the media.
        sensitive_warning : list{'adult_content', 'graphic_violence', 'other'}
            A list of sensitive content warnings for the media.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> media_id = await client.upload_media('media.jpg')
        >>> await client.create_media_metadata(
        ...     media_id,
        ...     alt_text='This is a sample media',
        ...     sensitive_warning=['other']
        ... )
        >>> await client.create_tweet(media_ids=[media_id])
        """
        _, response = await self.v11.create_media_metadata(media_id, alt_text, sensitive_warning)
        return response

    async def create_poll(
        self,
        choices: list[str],
        duration_minutes: int
    ) -> str:
        """
        Creates a poll and returns card-uri.

        Parameters
        ----------
        choices : list[:class:`str`]
            A list of choices for the poll. Maximum of 4 choices.
        duration_minutes : :class:`int`
            The duration of the poll in minutes.

        Returns
        -------
        :class:`str`
            The URI of the created poll card.

        Examples
        --------
        Create a poll with three choices lasting for 60 minutes:

        >>> choices = ['Option A', 'Option B', 'Option C']
        >>> duration_minutes = 60
        >>> card_uri = await client.create_poll(choices, duration_minutes)
        >>> print(card_uri)
        'card://0000000000000000000'
        """
        response, _ = await self.v11.create_card(choices, duration_minutes)
        return response['card_uri']

    async def vote(
        self,
        selected_choice: str,
        card_uri: str,
        tweet_id: str,
        card_name: str
    ) -> Poll:
        """
        Vote on a poll with the selected choice.
        Parameters
        ----------
        selected_choice : :class:`str`
            The label of the selected choice for the vote.
        card_uri : :class:`str`
            The URI of the poll card.
        tweet_id : :class:`str`
            The ID of the original tweet containing the poll.
        card_name : :class:`str`
            The name of the poll card.
        Returns
        -------
        :class:`Poll`
            The Poll object representing the updated poll after voting.
        """
        response, _ = await self.v11.vote(selected_choice, card_uri, tweet_id, card_name)
        card_data = {
            'rest_id': response['card']['url'],
            'legacy': response['card']
        }
        return Poll(self, card_data, None)

    async def create_tweet(
        self,
        text: str = '',
        media_ids: list[str] | None = None,
        poll_uri: str | None = None,
        reply_to: str | None = None,
        conversation_control: Literal['followers', 'verified', 'mentioned'] | None = None,
        attachment_url: str | None = None,
        community_id: str | None = None,
        share_with_followers: bool = False,
        is_note_tweet: bool = False,
        richtext_options: list[dict] = None,
        edit_tweet_id: str | None = None
    ) -> Tweet:
        """
        Creates a new tweet on Twitter with the specified
        text, media, and poll.

        Parameters
        ----------
        text : :class:`str`, default=''
            The text content of the tweet.
        media_ids : list[:class:`str`], default=None
            A list of media IDs or URIs to attach to the tweet.
            media IDs can be obtained by using the `upload_media` method.
        poll_uri : :class:`str`, default=None
            The URI of a Twitter poll card to attach to the tweet.
            Poll URIs can be obtained by using the `create_poll` method.
        reply_to : :class:`str`, default=None
            The ID of the tweet to which this tweet is a reply.
        conversation_control : {'followers', 'verified', 'mentioned'}
            The type of conversation control for the tweet:
            - 'followers': Limits replies to followers only.
            - 'verified': Limits replies to verified accounts only.
            - 'mentioned': Limits replies to mentioned accounts only.
        attachment_url : :class:`str`
            URL of the tweet to be quoted.
        is_note_tweet : :class:`bool`, default=False
            If this option is set to True, tweets longer than 280 characters
            can be posted (Twitter Premium only).
        richtext_options : list[:class:`dict`], default=None
            Options for decorating text (Twitter Premium only).
        edit_tweet_id : :class:`str` | None, default=None
            ID of the tweet to edit (Twitter Premium only).

        Raises
        ------
        :exc:`DuplicateTweet` : If the tweet is a duplicate of another tweet.

        Returns
        -------
        :class:`Tweet`
            The Created Tweet.

        Examples
        --------
        Create a tweet with media:

        >>> tweet_text = 'Example text'
        >>> media_ids = [
        ...     await client.upload_media('image1.png'),
        ...     await client.upload_media('image2.png')
        ... ]
        >>> await client.create_tweet(
        ...     tweet_text,
        ...     media_ids=media_ids
        ... )

        Create a tweet with a poll:

        >>> tweet_text = 'Example text'
        >>> poll_choices = ['Option A', 'Option B', 'Option C']
        >>> duration_minutes = 60
        >>> poll_uri = await client.create_poll(poll_choices, duration_minutes)
        >>> await client.create_tweet(
        ...     tweet_text,
        ...     poll_uri=poll_uri
        ... )

        See Also
        --------
        .upload_media
        .create_poll
        """
        media_entities = [
            {'media_id': media_id, 'tagged_users': []}
            for media_id in (media_ids or [])
        ]
        limit_mode = None
        if conversation_control is not None:
            conversation_control = conversation_control.lower()
            limit_mode = {
                'followers': 'Community',
                'verified': 'Verified',
                'mentioned': 'ByInvitation'
            }[conversation_control]

        response, _ = await self.gql.create_tweet(
            is_note_tweet, text, media_entities, poll_uri,
            reply_to, attachment_url, community_id, share_with_followers,
            richtext_options, edit_tweet_id, limit_mode
        )
        _result = response['data']['create_tweet']['tweet_results']
        if not _result:
            raise_exceptions_from_response(response['errors'])
            raise CouldNotTweet(
                response['errors'][0] if response['errors'] else 'Failed to post a tweet.'
            )
        return tweet_from_data(self, _result)

    async def create_scheduled_tweet(
        self,
        scheduled_at: int,
        text: str = '',
        media_ids: list[str] | None = None,
    ) -> str:
        """
        Schedules a tweet to be posted at a specified timestamp.

        Parameters
        ----------
        scheduled_at : :class:`int`
            The timestamp when the tweet should be scheduled for posting.
        text : :class:`str`, default=''
            The text content of the tweet, by default an empty string.
        media_ids : list[:class:`str`], default=None
            A list of media IDs to be attached to the tweet, by default None.

        Returns
        -------
        :class:`str`
            The ID of the scheduled tweet.

        Examples
        --------
        Create a tweet with media:

        >>> scheduled_time = int(time.time()) + 3600  # One hour from now
        >>> tweet_text = 'Example text'
        >>> media_ids = [
        ...     await client.upload_media('image1.png'),
        ...     await client.upload_media('image2.png')
        ... ]
        >>> await client.create_scheduled_tweet(
        ...     scheduled_time
        ...     tweet_text,
        ...     media_ids=media_ids
        ... )
        """
        response, _ = await self.gql.create_scheduled_tweet(scheduled_at, text, media_ids)
        return response['data']['tweet']['rest_id']

    async def delete_tweet(self, tweet_id: str) -> Response:
        """Deletes a tweet.

        Parameters
        ----------
        tweet_id : :class:`str`
            ID of the tweet to be deleted.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> tweet_id = '0000000000'
        >>> await delete_tweet(tweet_id)
        """
        _, response = await self.gql.delete_tweet(tweet_id)
        return response

    async def get_user_by_screen_name(self, screen_name: str) -> User:
        """
        Fetches a user by screen name.

        Parameter
        ---------
        screen_name : :class:`str`
            The screen name of the Twitter user.

        Returns
        -------
        :class:`User`
            An instance of the User class representing the
            Twitter user.

        Examples
        --------
        >>> target_screen_name = 'example_user'
        >>> user = await client.get_user_by_name(target_screen_name)
        >>> print(user)
        <User id="...">
        """
        response, _ = await self.gql.user_by_screen_name(screen_name)

        if 'user' not in response['data']:
            raise UserNotFound('The user does not exist.')
        user_data = response['data']['user']['result']
        if user_data.get('__typename') == 'UserUnavailable':
            raise UserUnavailable(user_data.get('message'))

        return User(self, user_data)

    async def get_user_by_id(self, user_id: str) -> User:
        """
        Fetches a user by ID

        Parameter
        ---------
        user_id : :class:`str`
            The ID of the Twitter user.

        Returns
        -------
        :class:`User`
            An instance of the User class representing the
            Twitter user.

        Examples
        --------
        >>> target_screen_name = '000000000'
        >>> user = await client.get_user_by_id(target_screen_name)
        >>> print(user)
        <User id="000000000">
        """
        response, _ = await self.gql.user_by_rest_id(user_id)
        if 'result' not in response['data']['user']:
            raise TwitterException(f'Invalid user id: {user_id}')
        user_data = response['data']['user']['result']
        if user_data.get('__typename') == 'UserUnavailable':
            raise UserUnavailable(user_data.get('message'))
        return User(self, user_data)

    async def reverse_geocode(
        self, lat: float, long: float, accuracy: str | float | None = None,
        granularity: str | None = None, max_results: int | None = None
    ) -> list[Place]:
        """
        Given a latitude and a longitude, searches for up to 20 places that

        Parameters
        ----------
        lat : :class:`float`
            The latitude to search around.
        long : :class:`float`
            The longitude to search around.
        accuracy : :class:`str` | :class:`float` None, default=None
            A hint on the "region" in which to search.
        granularity : :class:`str` | None, default=None
            This is the minimal granularity of place types to return and must
            be one of: `neighborhood`, `city`, `admin` or `country`.
        max_results : :class:`int` | None, default=None
            A hint as to the number of results to return.

        Returns
        -------
        list[:class:`.Place`]
        """
        response, _ = await self.v11.reverse_geocode(lat, long, accuracy, granularity, max_results)
        return _places_from_response(self, response)

    async def search_geo(
        self, lat: float | None = None, long: float | None = None,
        query: str | None = None, ip: str | None = None,
        granularity: str | None = None, max_results: int | None = None
    ) -> list[Place]:
        """
        Search for places that can be attached to a Tweet via POST
        statuses/update.

        Parameters
        ----------
        lat : :class:`float` | None
            The latitude to search around.
        long : :class:`float` | None
            	The longitude to search around.
        query : :class:`str` | None
            Free-form text to match against while executing a geo-based query,
            best suited for finding nearby locations by name.
            Remember to URL encode the query.
        ip : :class:`str` | None
            An IP address. Used when attempting to
            fix geolocation based off of the user's IP address.
        granularity : :class:`str` | None
            This is the minimal granularity of place types to return and must
            be one of: `neighborhood`, `city`, `admin` or `country`.
        max_results : :class:`int` | None
            A hint as to the number of results to return.

        Returns
        -------
        list[:class:`.Place`]
        """
        response, _ = await self.v11.search_geo(lat, long, query, ip, granularity, max_results)
        return _places_from_response(self, response)

    async def get_place(self, id: str) -> Place:
        """
        Parameters
        ----------
        id : :class:`str`
            The ID of the place.

        Returns
        -------
        :class:`.Place`
        """
        response, _ = await self.v11.get_place(id)
        return Place(self, response)

    async def _get_more_replies(
        self, tweet_id: str, cursor: str
    ) -> Result[Tweet]:
        response, _ = await self.gql.tweet_detail(tweet_id, cursor)
        entries = find_dict(response, 'entries', find_one=True)[0]

        results = []
        for entry in entries:
            if entry['entryId'].startswith(('cursor', 'label')):
                continue
            tweet = tweet_from_data(self, entry)
            if tweet is not None:
                results.append(tweet)

        if entries[-1]['entryId'].startswith('cursor'):
            next_cursor = entries[-1]['content']['itemContent']['value']
            _fetch_next_result = partial(self._get_more_replies, tweet_id, next_cursor)
        else:
            next_cursor = None
            _fetch_next_result = None

        return Result(
            results,
            _fetch_next_result,
            next_cursor
        )

    async def _show_more_replies(
        self, tweet_id: str, cursor: str
    ) -> Result[Tweet]:
        response, _ = await self.gql.tweet_detail(tweet_id, cursor)
        items = find_dict(response, 'moduleItems', find_one=True)[0]
        results = []
        for item in items:
            if 'tweet' not in item['entryId']:
                continue
            tweet = tweet_from_data(self, item)
            if tweet is not None:
                results.append(tweet)
        return Result(results)

    async def get_tweet_by_id(
        self, tweet_id: str, cursor: str | None = None
    ) -> Tweet:
        """
        Fetches a tweet by tweet ID.

        Parameters
        ----------
        tweet_id : :class:`str`
            The ID of the tweet.

        Returns
        -------
        :class:`Tweet`
            A Tweet object representing the fetched tweet.

        Examples
        --------
        >>> target_tweet_id = '...'
        >>> tweet = client.get_tweet_by_id(target_tweet_id)
        >>> print(tweet)
        <Tweet id="...">
        """
        response, _ = await self.gql.tweet_detail(tweet_id, cursor)

        if 'errors' in response:
            raise TweetNotAvailable(response['errors'][0]['message'])

        entries = find_dict(response, 'entries', find_one=True)[0]
        reply_to = []
        replies_list = []
        related_tweets = []
        tweet = None

        for entry in entries:
            if entry['entryId'].startswith('cursor'):
                continue
            tweet_object = tweet_from_data(self, entry)
            if tweet_object is None:
                continue

            if entry['entryId'].startswith('tweetdetailrelatedtweets'):
                related_tweets.append(tweet_object)
                continue

            if entry['entryId'] == f'tweet-{tweet_id}':
                tweet = tweet_object
            else:
                if tweet is None:
                    reply_to.append(tweet_object)
                else:
                    replies = []
                    sr_cursor = None
                    show_replies = None

                    for reply in entry['content']['items'][1:]:
                        if 'tweetcomposer' in reply['entryId']:
                            continue
                        if 'tweet' in reply.get('entryId'):
                            rpl = tweet_from_data(self, reply)
                            if rpl is None:
                                continue
                            replies.append(rpl)
                        if 'cursor' in reply.get('entryId'):
                            sr_cursor = reply['item']['itemContent']['value']
                            show_replies = partial(
                                self._show_more_replies,
                                tweet_id,
                                sr_cursor
                            )
                    tweet_object.replies = Result(
                        replies,
                        show_replies,
                        sr_cursor
                    )
                    replies_list.append(tweet_object)

                    display_type = find_dict(entry, 'tweetDisplayType', True)
                    if display_type and display_type[0] == 'SelfThread':
                        tweet.thread = [tweet_object, *replies]

        if entries[-1]['entryId'].startswith('cursor'):
            # if has more replies
            reply_next_cursor = entries[-1]['content']['itemContent']['value']
            _fetch_more_replies = partial(self._get_more_replies,
                                          tweet_id, reply_next_cursor)
        else:
            reply_next_cursor = None
            _fetch_more_replies = None

        tweet.replies = Result(
            replies_list,
            _fetch_more_replies,
            reply_next_cursor
        )
        tweet.reply_to = reply_to
        tweet.related_tweets = related_tweets

        return tweet

    async def get_scheduled_tweets(self) -> list[ScheduledTweet]:
        """
        Retrieves scheduled tweets.

        Returns
        -------
        list[:class:`ScheduledTweet`]
            List of ScheduledTweet objects representing the scheduled tweets.
        """
        response, _ = await self.gql.fetch_scheduled_tweets()
        tweets = find_dict(response, 'scheduled_tweet_list', find_one=True)[0]
        return [ScheduledTweet(self, tweet) for tweet in tweets]

    async def delete_scheduled_tweet(self, tweet_id: str) -> Response:
        """
        Delete a scheduled tweet.

        Parameters
        ----------
        tweet_id : :class:`str`
            The ID of the scheduled tweet to delete.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.
        """
        _, response = await self.gql.delete_scheduled_tweet(tweet_id)
        return response

    async def _get_tweet_engagements(
        self, tweet_id: str, count: int, cursor: str, f
    ) -> Result[User]:
        """
        Base function to get tweet engagements.
        type0: retweeters
        type1: favoriters
        """
        response, _ = await f(tweet_id, count, cursor)
        items_ = find_dict(response, 'entries', True)
        if not items_:
            return Result([])
        items = items_[0]
        next_cursor = items[-1]['content']['value']
        previous_cursor = items[-2]['content']['value']

        results = []
        for item in items:
            if not item['entryId'].startswith('user'):
                continue
            user_info_ = find_dict(item, 'result', True)
            if not user_info_:
                continue
            user_info = user_info_[0]
            results.append(User(self, user_info))

        return Result(
            results,
            partial(self._get_tweet_engagements, tweet_id, count, next_cursor, f),
            next_cursor,
            partial(self._get_tweet_engagements, tweet_id, count, previous_cursor, f),
            previous_cursor
        )

    async def get_retweeters(
        self, tweet_id: str, count: int = 40, cursor: str | None = None
    ) -> Result[User]:
        """
        Retrieve users who retweeted a specific tweet.

        Parameters
        ----------
        tweet_id : :class:`str`
            The ID of the tweet.
        count : :class:`int`, default=40
            The maximum number of users to retrieve.
        cursor : :class:`str`, default=None
            A string indicating the position of the cursor for pagination.

        Returns
        -------
        Result[:class:`User`]
            A list of users who retweeted the tweet.

        Examples
        --------
        >>> tweet_id = '...'
        >>> retweeters = client.get_retweeters(tweet_id)
        >>> print(retweeters)
        [<User id="...">, <User id="...">, ..., <User id="...">]

        >>> more_retweeters = retweeters.next()  # Retrieve more retweeters.
        >>> print(more_retweeters)
        [<User id="...">, <User id="...">, ..., <User id="...">]
        """
        return await self._get_tweet_engagements(tweet_id, count, cursor, self.gql.retweeters)

    async def get_favoriters(
        self, tweet_id: str, count: int = 40, cursor: str | None = None
    ) -> Result[User]:
        """
        Retrieve users who favorited a specific tweet.

        Parameters
        ----------
        tweet_id : :class:`str`
            The ID of the tweet.
        count : int, default=40
            The maximum number of users to retrieve.
        cursor : :class:`str`, default=None
            A string indicating the position of the cursor for pagination.

        Returns
        -------
        Result[:class:`User`]
            A list of users who favorited the tweet.

        Examples
        --------
        >>> tweet_id = '...'
        >>> favoriters = await client.get_favoriters(tweet_id)
        >>> print(favoriters)
        [<User id="...">, <User id="...">, ..., <User id="...">]

        >>> # Retrieve more favoriters.
        >>> more_favoriters = await favoriters.next()
        >>> print(more_favoriters)
        [<User id="...">, <User id="...">, ..., <User id="...">]
        """
        return await self._get_tweet_engagements(tweet_id, count, cursor, self.gql.favoriters)

    async def get_community_note(self, note_id: str) -> CommunityNote:
        """
        Fetches a community note by ID.

        Parameters
        ----------
        note_id : :class:`str`
            The ID of the community note.

        Returns
        -------
        :class:`CommunityNote`
            A CommunityNote object representing the fetched community note.

        Raises
        ------
        :exc:`TwitterException`
            Invalid note ID.

        Examples
        --------
        >>> note_id = '...'
        >>> note = client.get_community_note(note_id)
        >>> print(note)
        <CommunityNote id="...">
        """
        response, _ = await self.gql.bird_watch_one_note(note_id)
        note_data = response['data']['birdwatch_note_by_rest_id']
        if 'data_v1' not in note_data:
            raise TwitterException(f'Invalid note id: {note_id}')
        return CommunityNote(self, note_data)

    async def get_user_tweets(
        self,
        user_id: str,
        tweet_type: Literal['Tweets', 'Replies', 'Media', 'Likes'],
        count: int = 40,
        cursor: str | None = None
    ) -> Result[Tweet]:
        """
        Fetches tweets from a specific user's timeline.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the Twitter user whose tweets to retrieve.
            To get the user id from the screen name, you can use
            `get_user_by_screen_name` method.
        tweet_type : {'Tweets', 'Replies', 'Media', 'Likes'}
            The type of tweets to retrieve.
        count : :class:`int`, default=40
            The number of tweets to retrieve.
        cursor : :class:`str`, default=None
            The cursor for fetching the next set of results.

        Returns
        -------
        Result[:class:`Tweet`]
            A Result object containing a list of `Tweet` objects.

        Examples
        --------
        >>> user_id = '...'

        If you only have the screen name, you can get the user id as follows:

        >>> screen_name = 'example_user'
        >>> user = client.get_user_by_screen_name(screen_name)
        >>> user_id = user.id

        >>> tweets = await client.get_user_tweets(user_id, 'Tweets', count=20)
        >>> for tweet in tweets:
        ...    print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...

        >>> more_tweets = await tweets.next()  # Retrieve more tweets
        >>> for tweet in more_tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...

        >>> # Retrieve previous tweets
        >>> previous_tweets = await tweets.previous()

        See Also
        --------
        .get_user_by_screen_name
        """
        tweet_type = tweet_type.capitalize()
        f = {
            'Tweets': self.gql.user_tweets,
            'Replies': self.gql.user_tweets_and_replies,
            'Media': self.gql.user_media,
            'Likes': self.gql.user_likes,
        }[tweet_type]
        response, _ = await f(user_id, count, cursor)

        instructions_ = find_dict(response, 'instructions', True)
        if not instructions_:
            return Result([])
        instructions = instructions_[0]

        items = instructions[-1]['entries']
        next_cursor = items[-1]['content']['value']
        previous_cursor = items[-2]['content']['value']

        if tweet_type == 'Media':
            if cursor is None:
                items = items[0]['content']['items']
            else:
                items = instructions[0]['moduleItems']

        results = []
        for item in items:
            entry_id = item['entryId']

            if not entry_id.startswith(('tweet', 'profile-conversation', 'profile-grid')):
                continue

            if entry_id.startswith('profile-conversation'):
                tweets = item['content']['items']
                replies = []
                for reply in tweets[1:]:
                    tweet_object = tweet_from_data(self, reply)
                    if tweet_object is None:
                        continue
                    replies.append(tweet_object)
                item = tweets[0]
            else:
                replies = None

            tweet = tweet_from_data(self, item)
            if tweet is None:
                continue
            tweet.replies = replies
            results.append(tweet)

        return Result(
            results,
            partial(self.get_user_tweets, user_id, tweet_type, count, next_cursor),
            next_cursor,
            partial(self.get_user_tweets, user_id, tweet_type, count, previous_cursor),
            previous_cursor
        )

    async def get_timeline(
        self,
        count: int = 20,
        seen_tweet_ids: list[str] | None = None,
        cursor: str | None = None
    ) -> Result[Tweet]:
        """
        Retrieves the timeline.
        Retrieves tweets from Home -> For You.

        Parameters
        ----------
        count : :class:`int`, default=20
            The number of tweets to retrieve.
        seen_tweet_ids : list[:class:`str`], default=None
            A list of tweet IDs that have been seen.
        cursor : :class:`str`, default=None
            A cursor for pagination.

        Returns
        -------
        Result[:class:`Tweet`]
            A Result object containing a list of Tweet objects.

        Example
        -------
        >>> tweets = await client.get_timeline()
        >>> for tweet in tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...
        >>> more_tweets = await tweets.next() # Retrieve more tweets
        >>> for tweet in more_tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...
        """
        response, _ = await self.gql.home_timeline(count, seen_tweet_ids, cursor)
        items = find_dict(response, 'entries', find_one=True)[0]
        next_cursor = items[-1]['content']['value']
        results = []

        for item in items:
            if 'itemContent' not in item['content']:
                continue
            tweet = tweet_from_data(self, item)
            if tweet is None:
                continue
            results.append(tweet)

        return Result(
            results,
            partial(self.get_timeline, count, seen_tweet_ids, next_cursor),
            next_cursor
        )

    async def get_latest_timeline(
        self,
        count: int = 20,
        seen_tweet_ids: list[str] | None = None,
        cursor: str | None = None
    ) -> Result[Tweet]:
        """
        Retrieves the timeline.
        Retrieves tweets from Home -> Following.

        Parameters
        ----------
        count : :class:`int`, default=20
            The number of tweets to retrieve.
        seen_tweet_ids : list[:class:`str`], default=None
            A list of tweet IDs that have been seen.
        cursor : :class:`str`, default=None
            A cursor for pagination.

        Returns
        -------
        Result[:class:`Tweet`]
            A Result object containing a list of Tweet objects.

        Example
        -------
        >>> tweets = await client.get_latest_timeline()
        >>> for tweet in tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...
        >>> more_tweets = await tweets.next() # Retrieve more tweets
        >>> for tweet in more_tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...
        """
        response, _ = await self.gql.home_latest_timeline(count, seen_tweet_ids, cursor)
        items = find_dict(response, 'entries', find_one=True)[0]
        next_cursor = items[-1]['content']['value']
        results = []

        for item in items:
            if 'itemContent' not in item['content']:
                continue
            tweet = tweet_from_data(self, item)
            if tweet is None:
                continue
            results.append(tweet)

        return Result(
            results,
            partial(self.get_latest_timeline, count, seen_tweet_ids, next_cursor),
            next_cursor
        )

    async def favorite_tweet(self, tweet_id: str) -> Response:
        """
        Favorites a tweet.

        Parameters
        ----------
        tweet_id : :class:`str`
            The ID of the tweet to be liked.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> tweet_id = '...'
        >>> await client.favorite_tweet(tweet_id)

        See Also
        --------
        .unfavorite_tweet
        """
        _, response = await self.gql.favorite_tweet(tweet_id)
        return response

    async def unfavorite_tweet(self, tweet_id: str) -> Response:
        """
        Unfavorites a tweet.

        Parameters
        ----------
        tweet_id : :class:`str`
            The ID of the tweet to be unliked.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> tweet_id = '...'
        >>> await client.unfavorite_tweet(tweet_id)

        See Also
        --------
        .favorite_tweet
        """
        _, response = await self.gql.unfavorite_tweet(tweet_id)
        return response

    async def retweet(self, tweet_id: str) -> Response:
        """
        Retweets a tweet.

        Parameters
        ----------
        tweet_id : :class:`str`
            The ID of the tweet to be retweeted.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> tweet_id = '...'
        >>> await client.retweet(tweet_id)

        See Also
        --------
        .delete_retweet
        """
        _, response = await self.gql.retweet(tweet_id)
        return response

    async def delete_retweet(self, tweet_id: str) -> Response:
        """
        Deletes the retweet.

        Parameters
        ----------
        tweet_id : :class:`str`
            The ID of the retweeted tweet to be unretweeted.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> tweet_id = '...'
        >>> await client.delete_retweet(tweet_id)

        See Also
        --------
        .retweet
        """
        _, response = await self.gql.delete_retweet(tweet_id)
        return response

    async def bookmark_tweet(
        self, tweet_id: str, folder_id: str | None = None
    ) -> Response:
        """
        Adds the tweet to bookmarks.

        Parameters
        ----------
        tweet_id : :class:`str`
            The ID of the tweet to be bookmarked.
        folder_id : :class:`str` | None, default=None
            The ID of the folder to add the bookmark to.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> tweet_id = '...'
        >>> await client.bookmark_tweet(tweet_id)
        """
        if folder_id is None:
            _, response = await self.gql.create_bookmark(tweet_id)
        else:
            _, response = await self.gql.bookmark_tweet_to_folder(tweet_id, folder_id)
        return response

    async def delete_bookmark(self, tweet_id: str) -> Response:
        """
        Removes the tweet from bookmarks.

        Parameters
        ----------
        tweet_id : :class:`str`
            The ID of the tweet to be removed from bookmarks.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> tweet_id = '...'
        >>> await client.delete_bookmark(tweet_id)

        See Also
        --------
        .bookmark_tweet
        """
        _, response = await self.gql.delete_bookmark(tweet_id)
        return response

    async def get_bookmarks(
        self, count: int = 20,
        cursor: str | None = None, folder_id: str | None = None
    ) -> Result[Tweet]:
        """
        Retrieves bookmarks from the authenticated user's Twitter account.

        Parameters
        ----------
        count : :class:`int`, default=20
            The number of bookmarks to retrieve.
        folder_id : :class:`str` | None, default=None
            Folder to retrieve bookmarks.

        Returns
        -------
        Result[:class:`Tweet`]
            A Result object containing a list of Tweet objects
            representing bookmarks.

        Example
        -------
        >>> bookmarks = await client.get_bookmarks()
        >>> for bookmark in bookmarks:
        ...     print(bookmark)
        <Tweet id="...">
        <Tweet id="...">

        >>> # # To retrieve more bookmarks
        >>> more_bookmarks = await bookmarks.next()
        >>> for bookmark in more_bookmarks:
        ...     print(bookmark)
        <Tweet id="...">
        <Tweet id="...">
        """
        if folder_id is None:
            response, _ = await self.gql.bookmarks(count, cursor)
        else:
            response, _ = await self.gql.bookmark_folder_timeline(count, cursor, folder_id)

        items_ = find_dict(response, 'entries', find_one=True)
        if not items_:
            return Result([])
        items = items_[0]
        next_cursor = items[-1]['content']['value']
        if folder_id is None:
            previous_cursor = items[-2]['content']['value']
            fetch_previous_result = partial(self.get_bookmarks, count, previous_cursor, folder_id)
        else:
            previous_cursor = None
            fetch_previous_result = None

        results = []
        for item in items:
            tweet = tweet_from_data(self, item)
            if tweet is None:
                continue
            results.append(tweet)

        return Result(
            results,
            partial(self.get_bookmarks, count, next_cursor, folder_id),
            next_cursor,
            fetch_previous_result,
            previous_cursor
        )

    async def delete_all_bookmarks(self) -> Response:
        """
        Deleted all bookmarks.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> await client.delete_all_bookmarks()
        """
        _, response = await self.gql.delete_all_bookmarks()
        return response

    async def get_bookmark_folders(self, cursor: str | None = None) -> Result[BookmarkFolder]:
        """
        Retrieves bookmark folders.

        Returns
        -------
        Result[:class:`BookmarkFolder`]
            Result object containing a list of bookmark folders.

        Examples
        --------
        >>> folders = await client.get_bookmark_folders()
        >>> print(folders)
        [<BookmarkFolder id="...">, ..., <BookmarkFolder id="...">]
        >>> more_folders = await folders.next()  # Retrieve more folders
        """
        response, _ = await self.gql.bookmark_folders_slice(cursor)

        slice = find_dict(response, 'bookmark_collections_slice', find_one=True)[0]
        results = []
        for item in slice['items']:
            results.append(BookmarkFolder(self, item))

        if 'next_cursor' in slice['slice_info']:
            next_cursor = slice['slice_info']['next_cursor']
            fetch_next_result = partial(self.get_bookmark_folders, next_cursor)
        else:
            next_cursor = None
            fetch_next_result = None

        return Result(
            results,
            fetch_next_result,
            next_cursor
        )

    async def edit_bookmark_folder(
        self, folder_id: str, name: str
    ) -> BookmarkFolder:
        """
        Edits a bookmark folder.

        Parameters
        ----------
        folder_id : :class:`str`
            ID of the folder to edit.
        name : :class:`str`
            New name for the folder.

        Returns
        -------
        :class:`BookmarkFolder`
            Updated bookmark folder.

        Examples
        --------
        >>> await client.edit_bookmark_folder('123456789', 'MyFolder')
        """
        response, _ = await self.gql.edit_bookmark_folder(folder_id, name)
        return BookmarkFolder(self, response['data']['bookmark_collection_update'])

    async def delete_bookmark_folder(self, folder_id: str) -> Response:
        """
        Deletes a bookmark folder.

        Parameters
        ----------
        folder_id : :class:`str`
            ID of the folder to delete.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.
        """
        _, response = await self.gql.delete_bookmark_folder(folder_id)
        return response

    async def create_bookmark_folder(self, name: str) -> BookmarkFolder:
        """Creates a bookmark folder.

        Parameters
        ----------
        name : :class:`str`
            Name of the folder.

        Returns
        -------
        :class:`BookmarkFolder`
            Newly created bookmark folder.
        """
        response, _ = await self.gql.create_bookmark_folder(name)
        return BookmarkFolder(self, response['data']['bookmark_collection_create'])

    async def follow_user(self, user_id: str) -> User:
        """
        Follows a user.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user to follow.

        Returns
        -------
        :class:`User`
            The followed user.

        Examples
        --------
        >>> user_id = '...'
        >>> await client.follow_user(user_id)

        See Also
        --------
        .unfollow_user
        """
        response, _ = await self.v11.create_friendships(user_id)
        return User(self, build_user_data(response))

    async def unfollow_user(self, user_id: str) -> User:
        """
        Unfollows a user.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user to unfollow.

        Returns
        -------
        :class:`User`
            The unfollowed user.

        Examples
        --------
        >>> user_id = '...'
        >>> await client.unfollow_user(user_id)

        See Also
        --------
        .follow_user
        """
        response, _ = await self.v11.destroy_friendships(user_id)
        return User(self, build_user_data(response))

    async def block_user(self, user_id: str) -> User:
        """
        Blocks a user.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user to block.

        Returns
        -------
        :class:`User`
            The blocked user.

        See Also
        --------
        .unblock_user
        """
        response, _ = await self.v11.create_blocks(user_id)
        return User(self, build_user_data(response))

    async def unblock_user(self, user_id: str) -> User:
        """
        Unblocks a user.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user to unblock.

        Returns
        -------
        :class:`User`
            The unblocked user.

        See Also
        --------
        .block_user
        """
        response, _ = await self.v11.destroy_blocks(user_id)
        return User(self, build_user_data(response))

    async def mute_user(self, user_id: str) -> User:
        """
        Mutes a user.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user to mute.

        Returns
        -------
        :class:`User`
            The muted user.

        See Also
        --------
        .unmute_user
        """
        response, _ = await self.v11.create_mutes(user_id)
        return User(self, build_user_data(response))

    async def unmute_user(self, user_id: str) -> User:
        """
        Unmutes a user.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user to unmute.

        Returns
        -------
        :class:`User`
            The unmuted user.

        See Also
        --------
        .mute_user
        """
        response, _ = await self.v11.destroy_mutes(user_id)
        return User(self, build_user_data(response))

    async def get_trends(
        self,
        category: Literal['trending', 'for-you', 'news', 'sports', 'entertainment'],
        count: int = 20,
        retry: bool = True,
        additional_request_params: dict | None = None
    ) -> list[Trend]:
        """
        Retrieves trending topics on Twitter.

        Parameters
        ----------
        category : {'trending', 'for-you', 'news', 'sports', 'entertainment'}
            The category of trends to retrieve. Valid options include:
            - 'trending': General trending topics.
            - 'for-you': Trends personalized for the user.
            - 'news': News-related trends.
            - 'sports': Sports-related trends.
            - 'entertainment': Entertainment-related trends.
        count : :class:`int`, default=20
            The number of trends to retrieve.
        retry : :class:`bool`, default=True
            If no trends are fetched continuously retry to fetch trends.
        additional_request_params : :class:`dict`, default=None
            Parameters to be added on top of the existing trends API
            parameters. Typically, it is used as `additional_request_params =
            {'candidate_source': 'trends'}` when this function doesn't work
            otherwise.

        Returns
        -------
        list[:class:`Trend`]
            A list of Trend objects representing the retrieved trends.

        Examples
        --------
        >>> trends = await client.get_trends('trending')
        >>> for trend in trends:
        ...     print(trend)
        <Trend name="...">
        <Trend name="...">
        ...
        """
        category = category.lower()
        if category in ['news', 'sports', 'entertainment']:
            category += '_unified'
        response, _ = await self.v11.guide(category, count, additional_request_params)

        entry_id_prefix = 'trends' if category == 'trending' else 'Guide'
        entries = [
            i for i in find_dict(response, 'entries', find_one=True)[0]
            if i['entryId'].startswith(entry_id_prefix)
        ]

        if not entries:
            if not retry:
                return []
            # Recall the method again, as the trend information
            # may not be returned due to a Twitter error.
            return await self.get_trends(category, count, retry, additional_request_params)

        items = entries[-1]['content']['timelineModule']['items']

        results = []
        for item in items:
            trend_info = item['item']['content']['trend']
            results.append(Trend(self, trend_info))

        return results

    async def get_available_locations(self) -> list[Location]:
        """
        Retrieves locations where trends can be retrieved.

        Returns
        -------
        list[:class:`.Location`]
        """
        response, _ = await self.v11.available_trends()
        return [Location(self, data) for data in response]

    async def get_place_trends(self, woeid: int) -> PlaceTrends:
        """
        Retrieves the top 50 trending topics for a specific id.
        You can get available woeid using
        :attr:`.Client.get_available_locations`.
        """
        response, _ = await self.v11.place_trends(woeid)
        trend_data = response[0]
        trends = [PlaceTrend(self, data) for data in trend_data['trends']]
        trend_data['trends'] = trends
        return trend_data

    async def _get_user_friendship(
        self,
        user_id: str,
        count: int,
        f,
        cursor: str | None
    ) -> Result[User]:
        """
        Base function to get friendship.
        """
        response, _ = await f(user_id, count, cursor)

        items_ = find_dict(response, 'entries', find_one=True)
        if not items_:
            return Result.empty()
        items = items_[0]
        results = []
        for item in items:
            entry_id = item['entryId']
            if entry_id.startswith('user'):
                user_info = find_dict(item, 'result', find_one=True)
                if not user_info:
                    warnings.warn(
                        'Some followers are excluded because '
                        '"Quality Filter" is enabled. To get all followers, '
                        'turn off it in the Twitter settings.'
                    )
                    continue
                if user_info[0].get('__typename') == 'UserUnavailable':
                    continue
                results.append(User(self, user_info[0]))
            elif entry_id.startswith('cursor-bottom'):
                next_cursor = item['content']['value']

        return Result(
            results,
            partial(self._get_user_friendship, user_id, count, f, next_cursor),
            next_cursor
        )

    async def _get_user_friendship_2(
        self, user_id: str, screen_name: str,
        count: int, f, cursor: str
    ) -> Result[User]:
        response, _ = await f(user_id, screen_name, count, cursor)
        users = response['users']
        results = []
        for user in users:
            results.append(User(self, build_user_data(user)))

        previous_cursor = response['previous_cursor']
        next_cursor = response['next_cursor']

        return Result(
            results,
            partial(self._get_user_friendship_2, user_id, screen_name, count, f, next_cursor),
            next_cursor,
            partial(self._get_user_friendship_2, user_id, screen_name, count, f, previous_cursor),
            previous_cursor
        )

    async def get_user_followers(
        self, user_id: str, count: int = 20, cursor: str | None = None
    ) -> Result[User]:
        """
        Retrieves a list of followers for a given user.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user for whom to retrieve followers.
        count : int, default=20
            The number of followers to retrieve.

        Returns
        -------
        Result[:class:`User`]
            A list of User objects representing the followers.
        """
        return await self._get_user_friendship(
            user_id, count, self.gql.followers, cursor
        )

    async def get_latest_followers(
        self, user_id: str | None = None, screen_name: str | None = None,
        count: int = 200, cursor: str | None = None
    ) -> Result[User]:
        """
        Retrieves the latest followers.
        Max count : 200
        """
        return await self._get_user_friendship_2(
            user_id, screen_name, count, self.v11.followers_list, cursor
        )

    async def get_latest_friends(
        self, user_id: str | None = None, screen_name: str | None = None,
        count: int = 200, cursor: str | None = None
    ) -> Result[User]:
        """
        Retrieves the latest friends (following users).
        Max count : 200
        """
        return await self._get_user_friendship_2(
            user_id, screen_name, count, self.v11.friends_list, cursor
        )

    async def get_user_verified_followers(
        self, user_id: str, count: int = 20, cursor: str | None = None
    ) -> Result[User]:
        """
        Retrieves a list of verified followers for a given user.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user for whom to retrieve verified followers.
        count : :class:`int`, default=20
            The number of verified followers to retrieve.

        Returns
        -------
        Result[:class:`User`]
            A list of User objects representing the verified followers.
        """
        return await self._get_user_friendship(
            user_id, count, self.gql.blue_verified_followers, cursor
        )

    async def get_user_followers_you_know(
        self, user_id: str, count: int = 20, cursor: str | None = None
    ) -> Result[User]:
        """
        Retrieves a list of common followers.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user for whom to retrieve followers you might know.
        count : :class:`int`, default=20
            The number of followers you might know to retrieve.

        Returns
        -------
        Result[:class:`User`]
            A list of User objects representing the followers you might know.
        """
        return await self._get_user_friendship(
            user_id, count, self.gql.followers_you_know, cursor
        )

    async def get_user_following(
        self, user_id: str, count: int = 20, cursor: str | None = None
    ) -> Result[User]:
        """
        Retrieves a list of users whom the given user is following.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user for whom to retrieve the following users.
        count : :class:`int`, default=20
            The number of following users to retrieve.

        Returns
        -------
        Result[:class:`User`]
            A list of User objects representing the users being followed.
        """
        return await self._get_user_friendship(
            user_id, count, self.gql.following, cursor
        )

    async def get_user_subscriptions(
        self, user_id: str, count: int = 20, cursor: str | None = None
    ) -> Result[User]:
        """
        Retrieves a list of users to which the specified user is subscribed.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user for whom to retrieve subscriptions.
        count : :class:`int`, default=20
            The number of subscriptions to retrieve.

        Returns
        -------
        Result[:class:`User`]
            A list of User objects representing the subscribed users.
        """
        return await self._get_user_friendship(
            user_id, count, self.gql.user_creator_subscriptions, cursor
        )

    async def _get_friendship_ids(
        self,
        user_id: str | None,
        screen_name: str | None,
        count: int,
        f,
        cursor: str | None
    ) -> Result[int]:
        response, _ = await f(user_id, screen_name, count, cursor)
        previous_cursor = response['previous_cursor']
        next_cursor = response['next_cursor']

        return Result(
            response['ids'],
            partial(self._get_friendship_ids, user_id, screen_name, count, f, next_cursor),
            next_cursor,
            partial(self._get_friendship_ids, user_id, screen_name, count, f, previous_cursor),
            previous_cursor
        )

    async def get_followers_ids(
        self,
        user_id: str | None = None,
        screen_name: str | None = None,
        count: int = 5000,
        cursor: str | None = None
    ) -> Result[int]:
        """
        Fetches the IDs of the followers of a specified user.

        Parameters
        ----------
        user_id : :class:`str` | None, default=None
            The ID of the user for whom to return results.
        screen_name : :class:`str` | None, default=None
            The screen name of the user for whom to return results.
        count : :class:`int`, default=5000
            The maximum number of IDs to retrieve.

        Returns
        -------
        :class:`Result`[:class:`int`]
            A Result object containing the IDs of the followers.
        """
        return await self._get_friendship_ids(user_id, screen_name, count, self.v11.followers_ids, cursor)

    async def get_friends_ids(
        self,
        user_id: str | None = None,
        screen_name: str | None = None,
        count: int = 5000,
        cursor: str | None = None
    ) -> Result[int]:
        """
        Fetches the IDs of the friends (following users) of a specified user.

        Parameters
        ----------
        user_id : :class:`str` | None, default=None
            The ID of the user for whom to return results.
        screen_name : :class:`str` | None, default=None
            The screen name of the user for whom to return results.
        count : :class:`int`, default=5000
            The maximum number of IDs to retrieve.

        Returns
        -------
        :class:`Result`[:class:`int`]
            A Result object containing the IDs of the friends.
        """
        return await self._get_friendship_ids(
            user_id, screen_name, count, self.v11.friends_ids, cursor
        )

    async def _send_dm(
        self,
        conversation_id: str,
        text: str,
        media_id: str | None,
        reply_to: str | None
    ) -> dict:
        """
        Base function to send dm.
        """
        response, _ = await self.v11.dm_new(conversation_id, text, media_id, reply_to)
        return response

    async def _get_dm_history(
        self,
        conversation_id: str,
        max_id: str | None = None
    ) -> dict:
        """
        Base function to get dm history.
        """
        response, _ = await self.v11.dm_conversation(conversation_id, max_id)
        return response

    async def send_dm(
        self,
        user_id: str,
        text: str,
        media_id: str | None = None,
        reply_to: str | None = None
    ) -> Message:
        """
        Send a direct message to a user.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user to whom the direct message will be sent.
        text : :class:`str`
            The text content of the direct message.
        media_id : :class:`str`, default=None
            The media ID associated with any media content
            to be included in the message.
            Media ID can be received by using the :func:`.upload_media` method.
        reply_to : :class:`str`, default=None
            Message ID to reply to.

        Returns
        -------
        :class:`Message`
            `Message` object containing information about the message sent.

        Examples
        --------
        >>> # send DM with media
        >>> user_id = '000000000'
        >>> media_id = await client.upload_media('image.png')
        >>> message = await client.send_dm(user_id, 'text', media_id)
        >>> print(message)
        <Message id='...'>

        See Also
        --------
        .upload_media
        .delete_dm
        """
        response = await self._send_dm(
            f'{user_id}-{await self.user_id()}', text, media_id, reply_to
        )

        message_data = find_dict(response, 'message_data', find_one=True)[0]
        users = list(response['users'].values())
        return Message(
            self,
            message_data,
            users[0]['id_str'],
            users[1]['id_str'] if len(users) == 2 else users[0]['id_str']
        )

    async def add_reaction_to_message(
        self, message_id: str, conversation_id: str, emoji: str
    ) -> Response:
        """
        Adds a reaction emoji to a specific message in a conversation.

        Parameters
        ----------
        message_id : :class:`str`
            The ID of the message to which the reaction emoji will be added.
            Group ID ('00000000') or partner_ID-your_ID ('00000000-00000001')
        conversation_id : :class:`str`
            The ID of the conversation containing the message.
        emoji : :class:`str`
            The emoji to be added as a reaction.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> message_id = '00000000'
        >>> conversation_id = f'00000001-{await client.user_id()}'
        >>> await client.add_reaction_to_message(
        ...    message_id, conversation_id, 'Emoji here'
        ... )
        """
        _, response = await self.gql.user_dm_reaction_mutation_add_mutation(
            message_id, conversation_id, emoji
        )
        return response

    async def remove_reaction_from_message(
        self, message_id: str, conversation_id: str, emoji: str
    ) -> Response:
        """
        Remove a reaction from a message.

        Parameters
        ----------
        message_id : :class:`str`
            The ID of the message from which to remove the reaction.
        conversation_id : :class:`str`
            The ID of the conversation where the message is located.
            Group ID ('00000000') or partner_ID-your_ID ('00000000-00000001')
        emoji : :class:`str`
            The emoji to remove as a reaction.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> message_id = '00000000'
        >>> conversation_id = f'00000001-{await client.user_id()}'
        >>> await client.remove_reaction_from_message(
        ...    message_id, conversation_id, 'Emoji here'
        ... )
        """
        _, response = await self.gql.user_dm_reaction_mutation_remove_mutation(
            message_id, conversation_id, emoji
        )
        return response

    async def delete_dm(self, message_id: str) -> Response:
        """
        Deletes a direct message with the specified message ID.

        Parameters
        ----------
        message_id : :class:`str`
            The ID of the direct message to be deleted.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> await client.delete_dm('0000000000')
        """
        _, response = await self.gql.dm_message_delete_mutation(message_id)
        return response

    async def get_dm_history(
        self,
        user_id: str,
        max_id: str | None = None
    ) -> Result[Message]:
        """
        Retrieves the DM conversation history with a specific user.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user with whom the DM conversation
            history will be retrieved.
        max_id : :class:`str`, default=None
            If specified, retrieves messages older than the specified max_id.

        Returns
        -------
        Result[:class:`Message`]
            A Result object containing a list of Message objects representing
            the DM conversation history.

        Examples
        --------
        >>> messages = await client.get_dm_history('0000000000')
        >>> for message in messages:
        >>>     print(message)
        <Message id="...">
        <Message id="...">
        ...
        ...

        >>> more_messages = await messages.next()  # Retrieve more messages
        >>> for message in more_messages:
        >>>     print(message)
        <Message id="...">
        <Message id="...">
        ...
        ...
        """
        response = await self._get_dm_history(
            f'{user_id}-{await self.user_id()}', max_id
        )

        items = response['conversation_timeline']['entries']
        if 'entries' not in response['conversation_timeline']:
            return Result([])

        messages = []
        for item in items:
            message_info = item['message']['message_data']
            messages.append(Message(
                self,
                message_info,
                message_info['sender_id'],
                message_info['recipient_id']
            ))

        return Result(
            messages,
            partial(self.get_dm_history, user_id, messages[-1].id),
            messages[-1].id
        )

    async def send_dm_to_group(
        self,
        group_id: str,
        text: str,
        media_id: str | None = None,
        reply_to: str | None = None
    ) -> GroupMessage:
        """
        Sends a message to a group.

        Parameters
        ----------
        group_id : :class:`str`
            The ID of the group in which the direct message will be sent.
        text : :class:`str`
            The text content of the direct message.
        media_id : :class:`str`, default=None
            The media ID associated with any media content
            to be included in the message.
            Media ID can be received by using the :func:`.upload_media` method.
        reply_to : :class:`str`, default=None
            Message ID to reply to.

        Returns
        -------
        :class:`GroupMessage`
            `GroupMessage` object containing information about
            the message sent.

        Examples
        --------
        >>> # send DM with media
        >>> group_id = '000000000'
        >>> media_id = await client.upload_media('image.png')
        >>> message = await client.send_dm_to_group(group_id, 'text', media_id)
        >>> print(message)
        <GroupMessage id='...'>

        See Also
        --------
        .upload_media
        .delete_dm
        """
        response = await self._send_dm(group_id, text, media_id, reply_to)

        message_data = find_dict(response, 'message_data', find_one=True)[0]
        users = list(response['users'].values())
        return GroupMessage(
            self,
            message_data,
            users[0]['id_str'],
            group_id
        )

    async def get_group_dm_history(
        self,
        group_id: str,
        max_id: str | None = None
    ) -> Result[GroupMessage]:
        """
        Retrieves the DM conversation history in a group.

        Parameters
        ----------
        group_id : :class:`str`
            The ID of the group in which the DM conversation
            history will be retrieved.
        max_id : :class:`str`, default=None
            If specified, retrieves messages older than the specified max_id.

        Returns
        -------
        Result[:class:`GroupMessage`]
            A Result object containing a list of GroupMessage objects
            representing the DM conversation history.

        Examples
        --------
        >>> messages = await client.get_group_dm_history('0000000000')
        >>> for message in messages:
        >>>     print(message)
        <GroupMessage id="...">
        <GroupMessage id="...">
        ...
        ...

        >>> more_messages = await messages.next()  # Retrieve more messages
        >>> for message in more_messages:
        >>>     print(message)
        <GroupMessage id="...">
        <GroupMessage id="...">
        ...
        ...
        """
        response = await self._get_dm_history(group_id, max_id)
        if 'entries' not in response['conversation_timeline']:
            return Result([])

        items = response['conversation_timeline']['entries']
        messages = []
        for item in items:
            if 'message' not in item:
                continue
            message_info = item['message']['message_data']
            messages.append(GroupMessage(
                self,
                message_info,
                message_info['sender_id'],
                group_id
            ))

        return Result(
            messages,
            partial(self.get_group_dm_history, group_id, messages[-1].id),
            messages[-1].id
        )

    async def get_group(self, group_id: str) -> Group:
        """
        Fetches a guild by ID.

        Parameters
        ----------
        group_id : :class:`str`
            The ID of the group to retrieve information for.

        Returns
        -------
        :class:`Group`
            An object representing the retrieved group.
        """
        response = await self._get_dm_history(group_id)
        return Group(self, group_id, response)

    async def add_members_to_group(
        self, group_id: str, user_ids: list[str]
    ) -> Response:
        """Adds members to a group.

        Parameters
        ----------
        group_id : :class:`str`
            ID of the group to which the member is to be added.
        user_ids : list[:class:`str`]
            List of IDs of users to be added.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> group_id = '...'
        >>> members = ['...']
        >>> await client.add_members_to_group(group_id, members)
        """
        _, response = await self.gql.add_participants_mutation(group_id, user_ids)
        return response

    async def change_group_name(self, group_id: str, name: str) -> Response:
        """Changes group name

        Parameters
        ----------
        group_id : :class:`str`
            ID of the group to be renamed.
        name : :class:`str`
            New name.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.
        """
        _, response = await self.v11.conversation_update_name(group_id, name)
        return response

    async def create_list(
        self, name: str, description: str = '', is_private: bool = False
    ) -> List:
        """
        Creates a list.

        Parameters
        ----------
        name : :class:`str`
            The name of the list.
        description : :class:`str`, default=''
            The description of the list.
        is_private : :class:`bool`, default=False
            Indicates whether the list is private (True) or public (False).

        Returns
        -------
        :class:`List`
            The created list.

        Examples
        --------
        >>> list = await client.create_list(
        ...     'list name',
        ...     'list description',
        ...     is_private=True
        ... )
        >>> print(list)
        <List id="...">
        """
        response, _ = await self.gql.create_list(name, description, is_private)
        list_info = find_dict(response, 'list', find_one=True)[0]
        return List(self, list_info)

    async def edit_list_banner(self, list_id: str, media_id: str) -> Response:
        """
        Edit the banner image of a list.

        Parameters
        ----------
        list_id : :class:`str`
            The ID of the list.
        media_id : :class:`str`
            The ID of the media to use as the new banner image.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> list_id = '...'
        >>> media_id = await client.upload_media('image.png')
        >>> await client.edit_list_banner(list_id, media_id)
        """
        _, response = await self.gql.edit_list_banner(list_id, media_id)
        return response

    async def delete_list_banner(self, list_id: str) -> Response:
        """Deletes list banner.

        Parameters
        ----------
        list_id : :class:`str`
            ID of the list from which the banner is to be removed.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.
        """
        _, response = await self.gql.delete_list_banner(list_id)
        return response

    async def edit_list(
        self,
        list_id: str,
        name: str | None = None,
        description: str | None = None,
        is_private: bool | None = None
    ) -> List:
        """
        Edits list information.

        Parameters
        ----------
        list_id : :class:`str`
            The ID of the list to edit.
        name : :class:`str`, default=None
            The new name for the list.
        description : :class:`str`, default=None
            The new description for the list.
        is_private : :class:`bool`, default=None
            Indicates whether the list should be private
            (True) or public (False).

        Returns
        -------
        :class:`List`
            The updated Twitter list.

        Examples
        --------
        >>> await client.edit_list(
        ...     'new name', 'new description', True
        ... )
        """
        response, _ = await self.gql.update_list(list_id, name, description, is_private)
        list_info = find_dict(response, 'list', find_one=True)[0]
        return List(self, list_info)

    async def add_list_member(self, list_id: str, user_id: str) -> List:
        """
        Adds a user to a list.

        Parameters
        ----------
        list_id : :class:`str`
            The ID of the list.
        user_id : :class:`str`
            The ID of the user to add to the list.

        Returns
        -------
        :class:`List`
            The updated Twitter list.

        Examples
        --------
        >>> await client.add_list_member('list id', 'user id')
        """
        response, _ = await self.gql.list_add_member(list_id, user_id)
        return List(self, response['data']['list'])

    async def remove_list_member(self, list_id: str, user_id: str) -> List:
        """
        Removes a user from a list.

        Parameters
        ----------
        list_id : :class:`str`
            The ID of the list.
        user_id : :class:`str`
            The ID of the user to remove from the list.

        Returns
        -------
        :class:`List`
            The updated Twitter list.

        Examples
        --------
        >>> await client.remove_list_member('list id', 'user id')
        """
        response, _ = await self.gql.list_remove_member(list_id, user_id)
        if 'errors' in response:
            raise TwitterException(response['errors'][0]['message'])
        return List(self, response['data']['list'])

    async def get_lists(
        self, count: int = 100, cursor: str = None
    ) -> Result[List]:
        """
        Retrieves a list of user lists.

        Parameters
        ----------
        count : :class:`int`
            The number of lists to retrieve.

        Returns
        -------
        Result[:class:`List`]
            Retrieved lists.

        Examples
        --------
        >>> lists = client.get_lists()
        >>> for list_ in lists:
        ...     print(list_)
        <List id="...">
        <List id="...">
        ...
        ...
        >>> more_lists = lists.next()  # Retrieve more lists
        """
        response, _ = await self.gql.list_management_pace_timeline(count, cursor)

        entries = find_dict(response, 'entries', find_one=True)[0]
        items = find_dict(entries, 'items')

        if len(items) < 2:
            return Result([])

        lists = []
        for list in items[1]:
            lists.append(List(self, list['item']['itemContent']['list']))

        next_cursor = entries[-1]['content']['value']

        return Result(
            lists,
            partial(self.get_lists, count, next_cursor),
            next_cursor
        )

    async def get_list(self, list_id: str) -> List:
        """
        Retrieve list by ID.

        Parameters
        ----------
        list_id : :class:`str`
            The ID of the list to retrieve.

        Returns
        -------
        :class:`List`
            List object.
        """
        response, _ = await self.gql.list_by_rest_id(list_id)
        list_data_ = find_dict(response, 'list', find_one=True)
        if not list_data_:
            raise ValueError(f'Invalid list id: {list_id}')
        return List(self, list_data_[0])

    async def get_list_tweets(
        self, list_id: str, count: int = 20, cursor: str | None = None
    ) -> Result[Tweet]:
        """
        Retrieves tweets from a list.

        Parameters
        ----------
        list_id : :class:`str`
            The ID of the list to retrieve tweets from.
        count : :class:`int`, default=20
            The number of tweets to retrieve.
        cursor : :class:`str`, default=None
            The cursor for pagination.

        Returns
        -------
        Result[:class:`Tweet`]
            A Result object containing the retrieved tweets.

        Examples
        --------
        >>> tweets = await client.get_list_tweets('list id')
        >>> for tweet in tweets:
        ...    print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...

        >>> more_tweets = await tweets.next()  # Retrieve more tweets
        >>> for tweet in more_tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...
        """
        response, _ = await self.gql.list_latest_tweets_timeline(list_id, count, cursor)

        items_ = find_dict(response, 'entries', find_one=True)
        if not items_:
            raise ValueError(f'Invalid list id: {list_id}')
        items = items_[0]
        next_cursor = items[-1]['content']['value']

        results = []
        for item in items:
            if not item['entryId'].startswith('tweet'):
                continue

            tweet = tweet_from_data(self, item)
            if tweet is not None:
                results.append(tweet)

        return Result(
            results,
            partial(self.get_list_tweets, list_id, count, next_cursor),
            next_cursor
        )

    async def _get_list_users(self, f: str, list_id: str, count: int, cursor: str) -> Result[User]:
        """
        Base function to retrieve the users associated with a list.
        """
        response, _ = await f(list_id, count, cursor)

        items = find_dict(response, 'entries', find_one=True)[0]
        results = []
        for item in items:
            entry_id = item['entryId']
            if entry_id.startswith('user'):
                user_info = find_dict(item, 'result', find_one=True)[0]
                results.append(User(self, user_info))
            elif entry_id.startswith('cursor-bottom'):
                next_cursor = item['content']['value']
                break

        return Result(
            results,
            partial(self._get_list_users, f, list_id, count, next_cursor),
            next_cursor
        )

    async def get_list_members(
        self, list_id: str, count: int = 20, cursor: str | None = None
    ) -> Result[User]:
        """Retrieves members of a list.

        Parameters
        ----------
        list_id : :class:`str`
            List ID.
        count : int, default=20
            Number of members to retrieve.

        Returns
        -------
        Result[:class:`User`]
            Members of a list

        Examples
        --------
        >>> members = client.get_list_members(123456789)
        >>> for member in members:
        ...     print(member)
        <User id="...">
        <User id="...">
        ...
        ...
        >>> more_members = members.next()  # Retrieve more members
        """
        return await self._get_list_users(self.gql.list_members, list_id, count, cursor)

    async def get_list_subscribers(
        self, list_id: str, count: int = 20, cursor: str | None = None
    ) -> Result[User]:
        """Retrieves subscribers of a list.

        Parameters
        ----------
        list_id : :class:`str`
            List ID.
        count : :class:`int`, default=20
            Number of subscribers to retrieve.

        Returns
        -------
        Result[:class:`User`]
            Subscribers of a list

        Examples
        --------
        >>> members = client.get_list_subscribers(123456789)
        >>> for subscriber in subscribers:
        ...     print(subscriber)
        <User id="...">
        <User id="...">
        ...
        ...
        >>> more_subscribers = members.next()  # Retrieve more subscribers
        """
        return await self._get_list_users(self.gql.list_subscribers, list_id, count, cursor)

    async def search_list(
        self, query: str, count: int = 20, cursor: str | None = None
    ) -> Result[List]:
        """
        Search for lists based on the provided query.

        Parameters
        ----------
        query : :class:`str`
            The search query.
        count : :class:`int`, default=20
            The number of lists to retrieve.

        Returns
        -------
        Result[:class:`List`]
            An instance of the `Result` class containing the
            search results.

        Examples
        --------
        >>> lists = await client.search_list('query')
        >>> for list in lists:
        ...     print(list)
        <List id="...">
        <List id="...">
        ...

        >>> more_lists = await lists.next()  # Retrieve more lists
        """
        response, _ = await self.gql.search_timeline(query, 'Lists', count, cursor)
        entries = find_dict(response, 'entries', find_one=True)[0]

        if cursor is None:
            items = entries[0]['content']['items']
        else:
            items = find_dict(response, 'moduleItems', find_one=True)[0]

        lists = []
        for item in items:
            lists.append(List(self, item['item']['itemContent']['list']))
        next_cursor = entries[-1]['content']['value']

        return Result(
            lists,
            partial(self.search_list, query, count, next_cursor),
            next_cursor
        )

    async def get_notifications(
        self,
        type: Literal['All', 'Verified', 'Mentions'],
        count: int = 40,
        cursor: str | None = None
    ) -> Result[Notification]:
        """
        Retrieve notifications based on the provided type.

        Parameters
        ----------
        type : {'All', 'Verified', 'Mentions'}
            Type of notifications to retrieve.
            All: All notifications
            Verified: Notifications relating to authenticated users
            Mentions: Notifications with mentions
        count : :class:`int`, default=40
            Number of notifications to retrieve.

        Returns
        -------
        Result[:class:`Notification`]
            List of retrieved notifications.

        Examples
        --------
        >>> notifications = await client.get_notifications('All')
        >>> for notification in notifications:
        ...     print(notification)
        <Notification id="...">
        <Notification id="...">
        ...
        ...

        >>> # Retrieve more notifications
        >>> more_notifications = await notifications.next()
        """
        type = type.capitalize()
        f = {
            'All': self.v11.notifications_all,
            'Verified': self.v11.notifications_verified,
            'Mentions': self.v11.notifications_mentions
        }[type]
        response, _ = await f(count, cursor)

        global_objects = response['globalObjects']
        users = {
            id: User(self, build_user_data(data))
            for id, data in global_objects.get('users', {}).items()
        }
        tweets = {}

        for id, tweet_data in global_objects.get('tweets', {}).items():
            user_id = tweet_data['user_id_str']
            user = users[user_id]
            tweet = Tweet(self, build_tweet_data(tweet_data), user)
            tweets[id] = tweet

        notifications = []

        for notification in global_objects.get('notifications', {}).values():
            user_actions = notification['template']['aggregateUserActionsV1']
            target_objects = user_actions['targetObjects']
            if target_objects and 'tweet' in target_objects[0]:
                tweet_id = target_objects[0]['tweet']['id']
                tweet = tweets[tweet_id]
            else:
                tweet = None

            from_users  = user_actions['fromUsers']
            if from_users and 'user' in from_users[0]:
                user_id = from_users[0]['user']['id']
                user = users[user_id]
            else:
                user = None

            notifications.append(Notification(self, notification, tweet, user))

        entries = find_dict(response, 'entries', find_one=True)[0]
        cursor_bottom_entry = [
            i for i in entries
            if i['entryId'].startswith('cursor-bottom')
        ]
        if cursor_bottom_entry:
            next_cursor = find_dict(cursor_bottom_entry[0], 'value', find_one=True)[0]
        else:
            next_cursor = None

        return Result(
            notifications,
            partial(self.get_notifications, type, count, next_cursor),
            next_cursor
        )

    async def search_community(
        self, query: str, cursor: str | None = None
    ) -> Result[Community]:
        """
        Searchs communities based on the specified query.

        Parameters
        ----------
        query : :class:`str`
            The search query.

        Returns
        -------
        Result[:class:`Community`]
            List of retrieved communities.

        Examples
        --------
        >>> communities = await client.search_communities('query')
        >>> for community in communities:
        ...     print(community)
        <Community id="...">
        <Community id="...">
        ...

        >>> # Retrieve more communities
        >>> more_communities = await communities.next()
        """
        response, _ = await self.gql.search_community(query, cursor)

        items = find_dict(response, 'items_results', find_one=True)[0]
        communities = []
        for item in items:
            communities.append(Community(self, item['result']))
        next_cursor_ = find_dict(response, 'next_cursor', find_one=True)
        next_cursor = next_cursor_[0] if next_cursor_ else None
        if next_cursor is None:
            fetch_next_result = None
        else:
            fetch_next_result = partial(self.search_community, query, next_cursor)
        return Result(
            communities,
            fetch_next_result,
            next_cursor
        )

    async def get_community(self, community_id: str) -> Community:
        """
        Retrieves community by ID.

        Parameters
        ----------
        list_id : :class:`str`
            The ID of the community to retrieve.

        Returns
        -------
        :class:`Community`
            Community object.
        """
        response, _ = await self.gql.community_query(community_id)
        community_data = find_dict(response, 'result', find_one=True)[0]
        return Community(self, community_data)

    async def get_community_tweets(
        self,
        community_id: str,
        tweet_type: Literal['Top', 'Latest', 'Media'],
        count: int = 40,
        cursor: str | None = None
    ) -> Result[Tweet]:
        """
        Retrieves tweets from a community.

        Parameters
        ----------
        community_id : :class:`str`
            The ID of the community.
        tweet_type : {'Top', 'Latest', 'Media'}
            The type of tweets to retrieve.
        count : :class:`int`, default=40
            The number of tweets to retrieve.

        Returns
        -------
        Result[:class:`Tweet`]
            List of retrieved tweets.

        Examples
        --------
        >>> community_id = '...'
        >>> tweets = await client.get_community_tweets(community_id, 'Latest')
        >>> for tweet in tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        >>> more_tweets = await tweets.next()  # Retrieve more tweets
        """
        if tweet_type == 'Media':
            response, _ = await self.gql.community_media_timeline(community_id, count, cursor)
        elif tweet_type == 'Top':
            response, _ = await self.gql.community_tweets_timeline(community_id, 'Relevance', count, cursor)
        elif tweet_type == 'Latest':
            response, _ = await self.gql.community_tweets_timeline(community_id, 'Recency', count, cursor)
        else:
            raise ValueError(f'Invalid tweet_type: {tweet_type}')

        entries = find_dict(response, 'entries', find_one=True)[0]
        if tweet_type == 'Media':
            if cursor is None:
                items = entries[0]['content']['items']
                next_cursor = entries[-1]['content']['value']
                previous_cursor = entries[-2]['content']['value']
            else:
                items = find_dict(response, 'moduleItems', find_one=True)[0]
                next_cursor = entries[-1]['content']['value']
                previous_cursor = entries[-2]['content']['value']
        else:
            items = entries
            next_cursor = items[-1]['content']['value']
            previous_cursor = items[-2]['content']['value']

        tweets = []
        for item in items:
            if not item['entryId'].startswith(('tweet', 'communities-grid')):
                continue

            tweet = tweet_from_data(self, item)
            if tweet is not None:
                tweets.append(tweet)

        return Result(
            tweets,
            partial(self.get_community_tweets, community_id, tweet_type, count, next_cursor),
            next_cursor,
            partial(self.get_community_tweets, community_id, tweet_type, count, previous_cursor),
            previous_cursor
        )

    async def get_communities_timeline(
        self, count: int = 20, cursor: str | None = None
    ) -> Result[Tweet]:
        """
        Retrieves tweets from communities timeline.

        Parameters
        ----------
        count : :class:`int`, default=20
            The number of tweets to retrieve.

        Returns
        -------
        Result[:class:`Tweet`]
            List of retrieved tweets.

        Examples
        --------
        >>> tweets = await client.get_communities_timeline()
        >>> for tweet in tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        >>> more_tweets = await tweets.next()  # Retrieve more tweets
        """
        response, _ = await self.gql.communities_main_page_timeline(count, cursor)
        items = find_dict(response, 'entries', find_one=True)[0]
        tweets = []
        for item in items:
            if not item['entryId'].startswith('tweet'):
                continue
            tweet_data = find_dict(item, 'result', find_one=True)[0]
            if 'tweet' in tweet_data:
                tweet_data = tweet_data['tweet']
            user_data = tweet_data['core']['user_results']['result']
            community_data = tweet_data['community_results']['result']
            community_data['rest_id'] = community_data['id_str']
            community = Community(self, community_data)
            tweet = Tweet(self, tweet_data, User(self, user_data))
            tweet.community = community
            tweets.append(tweet)

        next_cursor = items[-1]['content']['value']
        previous_cursor = items[-2]['content']['value']

        return Result(
            tweets,
            partial(self.get_communities_timeline, count, next_cursor),
            next_cursor,
            partial(self.get_communities_timeline, count, previous_cursor),
            previous_cursor
        )

    async def join_community(self, community_id: str) -> Community:
        """
        Join a community.

        Parameters
        ----------
        community_id : :class:`str`
            The ID of the community to join.

        Returns
        -------
        :class:`Community`
            The joined community.
        """
        response, _ = await self.gql.join_community(community_id)
        community_data = response['data']['community_join']
        community_data['rest_id'] = community_data['id_str']
        return Community(self, community_data)

    async def leave_community(self, community_id: str) -> Community:
        """
        Leave a community.

        Parameters
        ----------
        community_id : :class:`str`
            The ID of the community to leave.

        Returns
        -------
        :class:`Community`
            The left community.
        """
        response, _ = await self.gql.leave_community(community_id)
        community_data = response['data']['community_leave']
        community_data['rest_id'] = community_data['id_str']
        return Community(self, community_data)

    async def request_to_join_community(
        self, community_id: str, answer: str | None = None
    ) -> Community:
        """
        Request to join a community.

        Parameters
        ----------
        community_id : :class:`str`
            The ID of the community to request to join.
        answer : :class:`str`, default=None
            The answer to the join request.

        Returns
        -------
        :class:`Community`
            The requested community.
        """
        response, _ = await self.gql.request_to_join_community(community_id, answer)
        community_data = find_dict(response, 'result', find_one=True)[0]
        community_data['rest_id'] = community_data['id_str']
        return Community(self, community_data)

    async def _get_community_users(self, f, community_id: str, count: int, cursor: str | None):
        """
        Base function to retrieve community users.
        """
        response, _ = await f(community_id, count, cursor)

        items = find_dict(response, 'items_results', find_one=True)[0]
        users = []
        for item in items:
            if 'result' not in item:
                continue
            if item['result'].get('__typename') != 'User':
                continue
            users.append(CommunityMember(self, item['result']))

        next_cursor_ = find_dict(response, 'next_cursor', find_one=True)
        next_cursor = next_cursor_[0] if next_cursor_ else None

        if next_cursor is None:
            fetch_next_result = None
        else:
            fetch_next_result = partial(self._get_community_users, f, community_id, count, next_cursor)
        return Result(
            users,
            fetch_next_result,
            next_cursor
        )

    async def get_community_members(
        self, community_id: str, count: int = 20, cursor: str | None = None
    ) -> Result[CommunityMember]:
        """
        Retrieves members of a community.

        Parameters
        ----------
        community_id : :class:`str`
            The ID of the community.
        count : :class:`int`, default=20
            The number of members to retrieve.

        Returns
        -------
        Result[:class:`CommunityMember`]
            List of retrieved members.
        """
        return await self._get_community_users(
            self.gql.members_slice_timeline_query, community_id, count, cursor
        )

    async def get_community_moderators(
        self, community_id: str, count: int = 20, cursor: str | None = None
    ) -> Result[CommunityMember]:
        """
        Retrieves moderators of a community.

        Parameters
        ----------
        community_id : :class:`str`
            The ID of the community.
        count : :class:`int`, default=20
            The number of moderators to retrieve.

        Returns
        -------
        Result[:class:`CommunityMember`]
            List of retrieved moderators.
        """
        return await self._get_community_users(
            self.gql.moderators_slice_timeline_query, community_id, count, cursor
        )

    async def search_community_tweet(
        self,
        community_id: str,
        query: str,
        count: int = 20,
        cursor: str | None = None
    ) -> Result[Tweet]:
        """Searchs tweets in a community.

        Parameters
        ----------
        community_id : :class:`str`
            The ID of the community.
        query : :class:`str`
            The search query.
        count : :class:`int`, default=20
            The number of tweets to retrieve.

        Returns
        -------
        Result[:class:`Tweet`]
            List of retrieved tweets.
        """
        response, _ = await self.gql.community_tweet_search_module_query(community_id, query, count, cursor)

        items = find_dict(response, 'entries', find_one=True)[0]
        tweets = []
        for item in items:
            if not item['entryId'].startswith('tweet'):
                continue

            tweet = tweet_from_data(self, item)
            if tweet is not None:
                tweets.append(tweet)

        next_cursor = items[-1]['content']['value']
        previous_cursor = items[-2]['content']['value']

        return Result(
            tweets,
            partial(self.search_community_tweet, community_id, query, count, next_cursor),
            next_cursor,
            partial(self.search_community_tweet, community_id, query, count, previous_cursor),
            previous_cursor,
        )

    async def _stream(self, topics: set[str]) -> AsyncGenerator[tuple[str, Payload]]:
        url = 'https://api.twitter.com/live_pipeline/events'
        params = {'topics': ','.join(topics)}
        headers = self._base_headers
        headers.pop('content-type')

        async with self.http.stream('GET', url, params=params, headers=headers, timeout=None) as response:
            self._remove_duplicate_ct0_cookie()
            async for line in response.aiter_lines():
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                payload = _payload_from_data(data['payload'])
                yield data.get('topic'), payload

    async def get_streaming_session(
        self, topics: set[str], auto_reconnect: bool = True
    ) -> StreamingSession:
        """
        Returns a session for interacting with the streaming API.

        Parameters
        ----------
        topics : set[:class:`str`]
            The set of topics to stream.
            Topics can be generated using :class:`.Topic`.
        auto_reconnect : :class:`bool`, default=True
            Whether to automatically reconnect when disconnected.

        Returns
        -------
        :class:`.StreamingSession`
            A stream session instance.

        Examples
        --------
        >>> from twikit.streaming import Topic
        >>>
        >>> topics = {
        ...     Topic.tweet_engagement('1739617652'), # Stream tweet engagement
        ...     Topic.dm_update('17544932482-174455537996'), # Stream DM update
        ...     Topic.dm_typing('17544932482-174455537996') # Stream DM typing
        ... }
        >>> session = await client.get_streaming_session(topics)
        >>>
        >>> async for topic, payload in session:
        ...     if payload.dm_update:
        ...         conversation_id = payload.dm_update.conversation_id
        ...         user_id = payload.dm_update.user_id
        ...         print(f'{conversation_id}: {user_id} sent a message')
        >>>
        >>>     if payload.dm_typing:
        ...         conversation_id = payload.dm_typing.conversation_id
        ...         user_id = payload.dm_typing.user_id
        ...         print(f'{conversation_id}: {user_id} is typing')
        >>>
        >>>     if payload.tweet_engagement:
        ...         like = payload.tweet_engagement.like_count
        ...         retweet = payload.tweet_engagement.retweet_count
        ...         view = payload.tweet_engagement.view_count
        ...         print('Tweet engagement updated:'
        ...               f'likes: {like} retweets: {retweet} views: {view}')

        Topics to stream can be added or deleted using
        :attr:`.StreamingSession.update_subscriptions` method.

        >>> subscribe_topics = {
        ...     Topic.tweet_engagement('1749528513'),
        ...     Topic.tweet_engagement('1765829534')
        ... }
        >>> unsubscribe_topics = {
        ...     Topic.tweet_engagement('1739617652'),
        ...     Topic.dm_update('17544932482-174455537996'),
        ...     Topic.dm_update('17544932482-174455537996')
        ... }
        >>> await session.update_subscriptions(
        ...     subscribe_topics, unsubscribe_topics
        ... )

        See Also
        --------
        .StreamingSession
        .StreamingSession.update_subscriptions
        .Payload
        .Topic
        """
        stream = self._stream(topics)
        session_id = (await anext(stream))[1].config.session_id
        return StreamingSession(self, session_id, stream, topics, auto_reconnect)

    async def _update_subscriptions(
        self,
        session: StreamingSession,
        subscribe: set[str] | None = None,
        unsubscribe: set[str] | None = None
    ) -> Payload:
        if subscribe is None:
            subscribe = set()
        if unsubscribe is None:
            unsubscribe = set()

        response, _ = await self.v11.live_pipeline_update_subscriptions(
            session.id, ','.join(subscribe), ','.join(unsubscribe)
        )
        session.topics |= subscribe
        session.topics -= unsubscribe

        return _payload_from_data(response)

    async def _get_user_state(self) -> Literal['normal', 'bounced', 'suspended']:
        response, _ = await self.v11.user_state()
        return response['userState']
