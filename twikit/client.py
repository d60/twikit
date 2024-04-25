from __future__ import annotations

import io
import json
import time
import warnings
from functools import partial
from typing import Literal

import filetype
from fake_useragent import UserAgent
from httpx import Response

from .bookmark import BookmarkFolder
from .community import Community, CommunityMember
from .errors import (
    CouldNotTweet,
    InvalidMedia,
    TwitterException,
    UserNotFound,
    UserUnavailable,
    raise_exceptions_from_response,
)
from .group import Group, GroupMessage
from .http import HTTPClient
from .list import List
from .message import Message
from .notification import Notification
from .trend import Trend
from .tweet import CommunityNote, Poll, ScheduledTweet, Tweet, tweet_from_data
from .user import User
from .utils import (
    BOOKMARK_FOLDER_TIMELINE_FEATURES,
    COMMUNITY_TWEETS_FEATURES,
    COMMUNITY_NOTE_FEATURES,
    JOIN_COMMUNITY_FEATURES,
    LIST_FEATURES,
    FEATURES,
    TOKEN,
    USER_FEATURES,
    NOTE_TWEET_FEATURES,
    SIMILAR_POSTS_FEATURES,
    Endpoint,
    Flow,
    Result,
    build_tweet_data,
    build_user_data,
    find_dict,
    flatten_params,
    get_query_id,
    urlencode,
)


class Client:
    """
    A client for interacting with the Twitter API.

    Examples
    --------
    >>> client = Client(language='en-US')

    >>> client.login(
    ...     auth_info_1='example_user', auth_info_2='email@example.com', password='00000000'
    ... )
    """

    def __init__(self, language: str | None = None, proxies: dict | None = None, **kwargs) -> None:
        self._token = TOKEN
        self.language = language
        self.http = HTTPClient(proxies=proxies, **kwargs)
        self._user_id: str | None = None
        self._user_agent = UserAgent().random.strip()
        self._act_as: str | None = None

    def _get_guest_token(self) -> str:
        headers = self._base_headers
        headers.pop('X-Twitter-Active-User')
        headers.pop('X-Twitter-Auth-Type')
        response = self.http.post(Endpoint.GUEST_TOKEN, headers=headers, data={}).json()
        return response['guest_token']

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
            headers['X-Contributor-Version'] = '1'
        return headers

    def _get_csrf_token(self) -> str | None:
        """
        Retrieves the Cross-Site Request Forgery (CSRF) token from the
        current session's cookies.

        Returns
        -------
        str | None
            The CSRF token as a string.
        """
        return self.http.client.cookies.get('ct0')

    def login(self, *, auth_info_1: str, auth_info_2: str | None = None, password: str) -> dict:
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

        Examples
        --------
        >>> client.login(
        ...     auth_info_1='example_user', auth_info_2='email@example.com', password='00000000'
        ... )
        """
        self.http.client.cookies.clear()
        guest_token = self._get_guest_token()
        headers = self._base_headers | {'x-guest-token': guest_token}
        headers.pop('X-Twitter-Active-User')
        headers.pop('X-Twitter-Auth-Type')

        flow = Flow(self, Endpoint.LOGIN_FLOW, headers)

        flow.execute_task(params={'flow_name': 'login'})
        flow.execute_task()
        flow.execute_task(
            {
                'subtask_id': 'LoginEnterUserIdentifierSSO',
                'settings_list': {
                    'setting_responses': [
                        {
                            'key': 'user_identifier',
                            'response_data': {'text_data': {'result': auth_info_1}},
                        }
                    ],
                    'link': 'next_link',
                },
            }
        )

        if flow.task_id == 'LoginEnterAlternateIdentifierSubtask':
            flow.execute_task(
                {
                    'subtask_id': 'LoginEnterAlternateIdentifierSubtask',
                    'enter_text': {'text': auth_info_2, 'link': 'next_link'},
                }
            )

        flow.execute_task(
            {
                'subtask_id': 'LoginEnterPassword',
                'enter_password': {'password': password, 'link': 'next_link'},
            }
        )

        if flow.response is not None:
            if not flow.response['subtasks']:
                return

            self._user_id = find_dict(flow.response, 'id_str')[0]

            if flow.task_id == 'LoginTwoFactorAuthChallenge':
                print(find_dict(flow.response, 'secondary_text')[0]['text'])

                flow.execute_task(
                    {
                        'subtask_id': 'LoginTwoFactorAuthChallenge',
                        'enter_text': {'text': input('>>> '), 'link': 'next_link'},
                    }
                )

            if flow.task_id == 'LoginAcid':
                print(find_dict(flow.response, 'secondary_text')[0]['text'])

                flow.execute_task(
                    {
                        'subtask_id': 'LoginAcid',
                        'enter_text': {'text': input('>>> '), 'link': 'next_link'},
                    }
                )

            return flow.response
        raise TwitterException('Failed to login.')

    def logout(self) -> Response:
        """
        Logs out of the currently logged-in account.
        """
        return self.http.post(Endpoint.LOGOUT, headers=self._base_headers)

    def user_id(self) -> str:
        """
        Retrieves the user ID associated with the authenticated account.
        """
        if self._user_id is not None:
            return self._user_id
        response = self.http.get(Endpoint.SETTINGS, headers=self._base_headers).json()
        screen_name = response['screen_name']
        user = self.get_user_by_screen_name(screen_name)
        self._user_id = user.id
        return self._user_id

    def user(self) -> User:
        """
        Retrieve detailed information about the authenticated user.
        """
        return self.get_user_by_id(self.user_id())

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
        return dict(self.http.client.cookies)

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
            self.http.client.cookies.clear()
        self.http.client.cookies.update(cookies)

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

    def _search(self, query: str, product: str, count: int, cursor: str | None) -> dict:
        """
        Base search function.
        """
        variables = {
            'rawQuery': query,
            'count': count,
            'querySource': 'typed_query',
            'product': product,
        }
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({'variables': variables, 'features': FEATURES})
        return self.http.get(
            Endpoint.SEARCH_TIMELINE, params=params, headers=self._base_headers
        ).json()

    def search_tweet(
        self,
        query: str,
        product: Literal['Top', 'Latest', 'Media'],
        count: int = 20,
        cursor: str | None = None,
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
        >>> tweets = client.search_tweet('query', 'Top')
        >>> for tweet in tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...

        >>> more_tweets = tweets.next()  # Retrieve more tweets
        >>> for tweet in more_tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...

        >>> previous_tweets = tweets.previous()  # Retrieve previous tweets
        """
        product = product.capitalize()

        response = self._search(query, product, count, cursor)
        instructions = find_dict(response, 'instructions')
        if not instructions:
            return Result([])
        instructions = instructions[0]

        if product == 'Media' and cursor is not None:
            items = find_dict(instructions, 'moduleItems')[0]
        else:
            items_ = find_dict(instructions, 'entries')
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
                entries = find_dict(instructions, 'entries')[0]
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
            previous_cursor,
        )

    def search_user(self, query: str, count: int = 20, cursor: str | None = None) -> Result[User]:
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
        >>> result = client.search_user('query')
        >>> for user in result:
        ...     print(user)
        <User id="...">
        <User id="...">
        ...
        ...

        >>> more_results = result.next()  # Retrieve more search results
        >>> for user in more_results:
        ...     print(user)
        <User id="...">
        <User id="...">
        ...
        ...
        """
        response = self._search(query, 'People', count, cursor)
        items = find_dict(response, 'entries')[0]
        next_cursor = items[-1]['content']['value']

        results = []
        for item in items:
            if 'itemContent' not in item['content']:
                continue
            user_info = find_dict(item, 'result')[0]
            results.append(User(self, user_info))

        return Result(results, partial(self.search_user, query, count, next_cursor), next_cursor)

    def get_similar_tweets(self, tweet_id: str) -> list[Tweet]:
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
        params = flatten_params(
            {'variables': {'tweet_id': tweet_id}, 'features': SIMILAR_POSTS_FEATURES}
        )
        response = self.http.get(
            Endpoint.SIMILAR_POSTS, params=params, headers=self._base_headers
        ).json()
        items_ = find_dict(response, 'entries')
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

    def upload_media(
        self,
        source: str | bytes,
        wait_for_completion: bool = False,
        status_check_interval: float = 1.0,
        media_type: str | None = None,
        media_category: str | None = None,
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

        Returns
        -------
        :class:`str`
            The media ID of the uploaded media.

        Examples
        --------
        Videos, images and gifs can be uploaded.

        >>> media_id_1 = client.upload_media(
        ...     'media1.jpg',
        ... )

        >>> media_id_2 = client.upload_media('media2.mp4', wait_for_completion=True)

        >>> media_id_3 = client.upload_media(
        ...     'media3.gif',
        ...     wait_for_completion=True,
        ...     media_category='tweet_gif',  # media_category must be specified
        ... )
        """
        if not isinstance(wait_for_completion, bool):
            raise TypeError(
                'wait_for_completion must be bool,' f' not {wait_for_completion.__class__.__name__}'
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
                        '`media_category` must be specified to check the '
                        "upload status of gif images ('dm_gif' or 'tweet_gif')"
                    )
            elif media_type.startswith('image'):
                # Checking the upload status of an image is impossible.
                wait_for_completion = False

        total_bytes = len(binary)

        # ============ INIT =============
        params = {'command': 'INIT', 'total_bytes': total_bytes, 'media_type': media_type}
        if media_category is not None:
            params['media_category'] = media_category
        response = self.http.post(
            Endpoint.UPLOAD_MEDIA, params=params, headers=self._base_headers
        ).json()
        media_id = response['media_id']
        # =========== APPEND ============
        segment_index = 0
        bytes_sent = 0
        MAX_SEGMENT_SIZE = 8 * 1024 * 1024  # The maximum segment size is 8 MB

        while bytes_sent < total_bytes:
            chunk = binary[bytes_sent : bytes_sent + MAX_SEGMENT_SIZE]
            chunk_stream = io.BytesIO(chunk)
            params = {
                'command': 'APPEND',
                'media_id': media_id,
                'segment_index': segment_index,
            }
            headers = self._base_headers
            headers.pop('content-type')
            files = {
                'media': (
                    'blob',
                    chunk_stream,
                    'application/octet-stream',
                )
            }
            self.http.post(Endpoint.UPLOAD_MEDIA, params=params, headers=headers, files=files)

            chunk_stream.close()
            segment_index += 1
            bytes_sent += len(chunk)

        # ========== FINALIZE ===========
        params = {
            'command': 'FINALIZE',
            'media_id': media_id,
        }
        self.http.post(
            Endpoint.UPLOAD_MEDIA,
            params=params,
            headers=self._base_headers,
        )

        if wait_for_completion:
            while True:
                state = self.check_media_status(media_id)
                processing_info = state['processing_info']
                if 'error' in processing_info:
                    raise InvalidMedia(processing_info['error'].get('message'))
                if processing_info['state'] == 'succeeded':
                    break
                time.sleep(status_check_interval)

        return media_id

    def check_media_status(self, media_id: str) -> dict:
        """
        Check the status of uploaded media.

        Parameters
        ----------
        media_id : :class:`str`
            The media ID of the uploaded media.

        Returns
        -------
        :class:`dict`
            A dictionary containing information about the status of
            the uploaded media.
        """
        params = {'command': 'STATUS', 'media_id': media_id}
        return self.http.get(
            Endpoint.UPLOAD_MEDIA, params=params, headers=self._base_headers
        ).json()

    def create_media_metadata(
        self,
        media_id: str,
        alt_text: str | None = None,
        sensitive_warning: list[Literal['adult_content', 'graphic_violence', 'other']] = None,
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
        >>> media_id = client.upload_media('media.jpg')
        >>> client.create_media_metadata(
        ...     media_id, alt_text='This is a sample media', sensitive_warning=['other']
        ... )
        >>> client.create_tweet(media_ids=[media_id])
        """
        data = {'media_id': media_id}
        if alt_text is not None:
            data['alt_text'] = {'text': alt_text}
        if sensitive_warning is not None:
            data['sensitive_media_warning'] = sensitive_warning
        return self.http.post(Endpoint.CREATE_MEDIA_METADATA, json=data, headers=self._base_headers)

    def get_media(self, url: str) -> bytes:
        """Retrieves media bytes.

        Parameters
        ----------
        url : str
            Media URL
        """
        return self.http.get(url, headers=self._base_headers).content

    def create_poll(self, choices: list[str], duration_minutes: int) -> str:
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
        >>> card_uri = client.create_poll(choices, duration_minutes)
        >>> print(card_uri)
        'card://0000000000000000000'
        """
        card_data = {
            'twitter:card': f'poll{len(choices)}choice_text_only',
            'twitter:api:api:endpoint': '1',
            'twitter:long:duration_minutes': duration_minutes,
        }

        for i, choice in enumerate(choices, 1):
            card_data[f'twitter:string:choice{i}_label'] = choice

        data = urlencode({'card_data': card_data})
        headers = self._base_headers | {'content-type': 'application/x-www-form-urlencoded'}
        response = self.http.post(
            Endpoint.CREATE_CARD,
            data=data,
            headers=headers,
        ).json()

        return response['card_uri']

    def vote(self, selected_choice: str, card_uri: str, tweet_id: str, card_name: str) -> Poll:
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
        data = urlencode(
            {
                'twitter:string:card_uri': card_uri,
                'twitter:long:original_tweet_id': tweet_id,
                'twitter:string:response_card_name': card_name,
                'twitter:string:cards_platform': 'Web-12',
                'twitter:string:selected_choice': selected_choice,
            }
        )
        headers = self._base_headers | {'content-type': 'application/x-www-form-urlencoded'}
        response = self.http.post(Endpoint.VOTE, data=data, headers=headers).json()

        card_data = {'rest_id': response['card']['url'], 'legacy': response['card']}
        return Poll(self, card_data, None)

    def create_tweet(
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
        richtext_options: list[dict] | None = None,
        edit_tweet_id: str | None = None,
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
        is_note_tweet : class`bool`, default=False
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
        >>> media_ids = [client.upload_media('image1.png'), client.upload_media('image2.png')]
        >>> client.create_tweet(tweet_text, media_ids=media_ids)

        Create a tweet with a poll:

        >>> tweet_text = 'Example text'
        >>> poll_choices = ['Option A', 'Option B', 'Option C']
        >>> duration_minutes = 60
        >>> poll_uri = client.create_poll(poll_choices, duration_minutes)
        >>> client.create_tweet(tweet_text, poll_uri=poll_uri)

        See Also
        --------
        .upload_media
        .create_poll
        """
        media_entities = [
            {'media_id': media_id, 'tagged_users': []} for media_id in (media_ids or [])
        ]
        variables = {
            'tweet_text': text,
            'dark_request': False,
            'media': {'media_entities': media_entities, 'possibly_sensitive': False},
            'semantic_annotation_ids': [],
        }

        if poll_uri is not None:
            variables['card_uri'] = poll_uri

        if reply_to is not None:
            variables['reply'] = {'in_reply_to_tweet_id': reply_to, 'exclude_reply_user_ids': []}

        if conversation_control is not None:
            conversation_control = conversation_control.lower()
            limit_mode = {
                'followers': 'Community',
                'verified': 'Verified',
                'mentioned': 'ByInvitation',
            }[conversation_control]
            variables['conversation_control'] = {'mode': limit_mode}

        if attachment_url is not None:
            variables['attachment_url'] = attachment_url

        if community_id is not None:
            variables['semantic_annotation_ids'] = [
                {'entity_id': community_id, 'group_id': '8', 'domain_id': '31'}
            ]
            variables['broadcast'] = share_with_followers

        if richtext_options is not None:
            is_note_tweet = True
            variables['richtext_options'] = {'richtext_tags': richtext_options}

        if edit_tweet_id is not None:
            variables['edit_options'] = {'previous_tweet_id': edit_tweet_id}

        if is_note_tweet:
            endpoint = Endpoint.CREATE_NOTE_TWEET
            features = NOTE_TWEET_FEATURES
        else:
            endpoint = Endpoint.CREATE_TWEET
            features = FEATURES
        data = {
            'variables': variables,
            'queryId': get_query_id(Endpoint.CREATE_TWEET),
            'features': features,
        }
        response = self.http.post(
            endpoint,
            json=data,
            headers=self._base_headers,
        ).json()

        _result = find_dict(response, 'result')
        if not _result:
            raise_exceptions_from_response(response['errors'])
            raise CouldNotTweet(
                response['errors'][0] if response['errors'] else 'Failed to post a tweet.'
            )

        tweet_info = _result[0]
        user_info = tweet_info['core']['user_results']['result']
        return Tweet(self, tweet_info, User(self, user_info))

    def create_scheduled_tweet(
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
        >>> media_ids = [client.upload_media('image1.png'), client.upload_media('image2.png')]
        >>> client.create_scheduled_tweet(
        ...     scheduled_time
        ...     tweet_text,
        ...     media_ids=media_ids
        ... )
        """
        variables = {
            'post_tweet_request': {
                'auto_populate_reply_metadata': False,
                'status': text,
                'exclude_reply_user_ids': [],
                'media_ids': media_ids,
            },
            'execute_at': scheduled_at,
        }
        data = {
            'variables': variables,
            'queryId': get_query_id(Endpoint.CREATE_SCHEDULED_TWEET),
        }
        response = self.http.post(
            Endpoint.CREATE_SCHEDULED_TWEET,
            json=data,
            headers=self._base_headers,
        ).json()
        return response['data']['tweet']['rest_id']

    def delete_tweet(self, tweet_id: str) -> Response:
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
        >>> delete_tweet(tweet_id)
        """
        data = {
            'variables': {'tweet_id': tweet_id, 'dark_request': False},
            'queryId': get_query_id(Endpoint.DELETE_TWEET),
        }
        return self.http.post(Endpoint.DELETE_TWEET, json=data, headers=self._base_headers)

    def get_user_by_screen_name(self, screen_name: str) -> User:
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
        >>> user = client.get_user_by_name(target_screen_name)
        >>> print(user)
        <User id="...">
        """
        variables = {'screen_name': screen_name, 'withSafetyModeUserFields': False}
        params = flatten_params(
            {
                'variables': variables,
                'features': USER_FEATURES,
                'fieldToggles': {'withAuxiliaryUserLabels': False},
            }
        )
        response = self.http.get(
            Endpoint.USER_BY_SCREEN_NAME, params=params, headers=self._base_headers
        ).json()

        if 'user' not in response['data']:
            raise UserNotFound('The user does not exist.')
        user_data = response['data']['user']['result']
        if user_data.get('__typename') == 'UserUnavailable':
            raise UserUnavailable(user_data.get('message'))

        return User(self, user_data)

    def get_user_by_id(self, user_id: str) -> User:
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
        >>> user = client.get_user_by_id(target_screen_name)
        >>> print(user)
        <User id="000000000">
        """
        variables = {'userId': user_id, 'withSafetyModeUserFields': True}
        params = flatten_params({'variables': variables, 'features': USER_FEATURES})
        response = self.http.get(
            Endpoint.USER_BY_REST_ID, params=params, headers=self._base_headers
        ).json()
        if 'result' not in response['data']['user']:
            raise TwitterException(f'Invalid user id: {user_id}')
        user_data = response['data']['user']['result']
        if user_data.get('__typename') == 'UserUnavailable':
            raise UserUnavailable(user_data.get('message'))
        return User(self, user_data)

    def _get_tweet_detail(self, tweet_id: str, cursor: str | None):
        variables = {
            'focalTweetId': tweet_id,
            'with_rux_injections': False,
            'includePromotedContent': True,
            'withCommunity': True,
            'withQuickPromoteEligibilityTweetFields': True,
            'withBirdwatchNotes': True,
            'withVoice': True,
            'withV2Timeline': True,
        }
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params(
            {
                'variables': variables,
                'features': FEATURES,
                'fieldToggles': {'withAuxiliaryUserLabels': False},
            }
        )
        return self.http.get(
            Endpoint.TWEET_DETAIL, params=params, headers=self._base_headers
        ).json()

    def _get_more_replies(self, tweet_id: str, cursor: str) -> Result[Tweet]:
        response = self._get_tweet_detail(tweet_id, cursor)
        entries = find_dict(response, 'entries')[0]

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

        return Result(results, _fetch_next_result, next_cursor)

    def _show_more_replies(self, tweet_id: str, cursor: str) -> Result[Tweet]:
        response = self._get_tweet_detail(tweet_id, cursor)
        items = find_dict(response, 'moduleItems')[0]
        results = []
        for item in items:
            if 'tweet' not in item['entryId']:
                continue
            tweet = tweet_from_data(self, item)
            if tweet is not None:
                results.append(tweet)
        return Result(results)

    def get_tweet_by_id(self, tweet_id: str, cursor: str | None = None) -> Tweet:
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
        response = self._get_tweet_detail(tweet_id, cursor)

        entries = find_dict(response, 'entries')[0]
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
                            show_replies = partial(self._show_more_replies, tweet_id, sr_cursor)
                    tweet_object.replies = Result(replies, show_replies, sr_cursor)
                    replies_list.append(tweet_object)

                    display_type = find_dict(entry, 'tweetDisplayType', True)
                    if display_type and display_type[0] == 'SelfThread':
                        tweet.thread = [tweet_object, *replies]

        if entries[-1]['entryId'].startswith('cursor'):
            # if has more replies
            reply_next_cursor = entries[-1]['content']['itemContent']['value']
            _fetch_more_replies = partial(self._get_more_replies, tweet_id, reply_next_cursor)
        else:
            reply_next_cursor = None
            _fetch_more_replies = None

        tweet.replies = Result(replies_list, _fetch_more_replies, reply_next_cursor)
        tweet.reply_to = reply_to
        tweet.related_tweets = related_tweets

        return tweet

    def get_scheduled_tweets(self) -> list[ScheduledTweet]:
        """
        Retrieves scheduled tweets.

        Returns
        -------
        list[:class:`ScheduledTweet`]
            List of ScheduledTweet objects representing the scheduled tweets.
        """
        params = flatten_params({'variables': {'ascending': True}})
        response = self.http.get(
            Endpoint.FETCH_SCHEDULED_TWEETS, params=params, headers=self._base_headers
        ).json()
        tweets = find_dict(response, 'scheduled_tweet_list')[0]
        return [ScheduledTweet(self, tweet) for tweet in tweets]

    def delete_scheduled_tweet(self, tweet_id: str) -> Response:
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
        data = {
            'variables': {'scheduled_tweet_id': tweet_id},
            'queryId': get_query_id(Endpoint.DELETE_SCHEDULED_TWEET),
        }
        return self.http.post(
            Endpoint.DELETE_SCHEDULED_TWEET, json=data, headers=self._base_headers
        )

    def _get_tweet_engagements(
        self,
        tweet_id: str,
        count: int,
        cursor: str,
        endpoint: str,
    ) -> Result[User]:
        """
        Base function to get tweet engagements.
        """
        variables = {'tweetId': tweet_id, 'count': count, 'includePromotedContent': True}
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({'variables': variables, 'features': FEATURES})
        response = self.http.get(endpoint, params=params, headers=self._base_headers).json()
        items_ = find_dict(response, 'entries')
        if not items_:
            return Result([])
        items = items_[0]
        next_cursor = items[-1]['content']['value']
        previous_cursor = items[-2]['content']['value']

        results = []
        for item in items:
            if not item['entryId'].startswith('user'):
                continue
            user_info_ = find_dict(item, 'result')
            if not user_info_:
                continue
            user_info = user_info_[0]
            results.append(User(self, user_info))

        return Result(
            results,
            partial(self._get_tweet_engagements, tweet_id, count, next_cursor, endpoint),
            next_cursor,
            partial(self._get_tweet_engagements, tweet_id, count, previous_cursor, endpoint),
            previous_cursor,
        )

    def get_retweeters(
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
        return self._get_tweet_engagements(tweet_id, count, cursor, Endpoint.RETWEETERS)

    def get_favoriters(
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
        >>> favoriters = client.get_favoriters(tweet_id)
        >>> print(favoriters)
        [<User id="...">, <User id="...">, ..., <User id="...">]

        >>> more_favoriters = favoriters.next()  # Retrieve more favoriters.
        >>> print(more_favoriters)
        [<User id="...">, <User id="...">, ..., <User id="...">]
        """
        return self._get_tweet_engagements(tweet_id, count, cursor, Endpoint.FAVORITERS)

    def get_community_note(self, note_id: str) -> CommunityNote:
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
        params = flatten_params(
            {'variables': {'note_id': note_id}, 'features': COMMUNITY_NOTE_FEATURES}
        )
        response = self.http.get(
            Endpoint.FETCH_COMMUNITY_NOTE, params=params, headers=self._base_headers
        ).json()
        note_data = response['data']['birdwatch_note_by_rest_id']
        if 'data_v1' not in note_data:
            raise TwitterException(f'Invalid note id: {note_id}')
        return CommunityNote(self, note_data)

    def get_user_tweets(
        self,
        user_id: str,
        tweet_type: Literal['Tweets', 'Replies', 'Media', 'Likes'],
        count: int = 40,
        cursor: str | None = None,
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

        >>> tweets = client.get_user_tweets(user_id, 'Tweets', count=20)
        >>> for tweet in tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...

        >>> more_tweets = tweets.next()  # Retrieve more tweets
        >>> for tweet in more_tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...

        >>> previous_tweets = tweets.previous()  # Retrieve previous tweets

        See Also
        --------
        .get_user_by_screen_name
        """
        tweet_type = tweet_type.capitalize()

        variables = {
            'userId': user_id,
            'count': count,
            'includePromotedContent': True,
            'withQuickPromoteEligibilityTweetFields': True,
            'withVoice': True,
            'withV2Timeline': True,
        }
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({'variables': variables, 'features': FEATURES})
        endpoint = {
            'Tweets': Endpoint.USER_TWEETS,
            'Replies': Endpoint.USER_TWEETS_AND_REPLIES,
            'Media': Endpoint.USER_MEDIA,
            'Likes': Endpoint.USER_LIKES,
        }[tweet_type]

        response = self.http.get(endpoint, params=params, headers=self._base_headers).json()

        instructions_ = find_dict(response, 'instructions')
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
            previous_cursor,
        )

    def get_timeline(
        self, count: int = 20, seen_tweet_ids: list[str] | None = None, cursor: str | None = None
    ) -> Result[Tweet]:
        """
        Retrieves the timeline.
        Retrieves tweets from Home -> For You.

        Parameters
        ----------
        count : int, default=20
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
        >>> tweets = client.get_timeline()
        >>> for tweet in tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...
        >>> more_tweets = tweets.next()  # Retrieve more tweets
        >>> for tweet in more_tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...
        """
        variables = {
            'count': count,
            'includePromotedContent': True,
            'latestControlAvailable': True,
            'requestContext': 'launch',
            'withCommunity': True,
            'seenTweetIds': seen_tweet_ids or [],
        }
        if cursor is not None:
            variables['cursor'] = cursor

        data = {
            'variables': variables,
            'queryId': get_query_id(Endpoint.HOME_TIMELINE),
            'features': FEATURES,
        }
        response = self.http.post(
            Endpoint.HOME_TIMELINE, json=data, headers=self._base_headers
        ).json()

        items = find_dict(response, 'entries')[0]
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
            results, partial(self.get_timeline, count, seen_tweet_ids, next_cursor), next_cursor
        )

    def get_latest_timeline(
        self, count: int = 20, seen_tweet_ids: list[str] | None = None, cursor: str | None = None
    ) -> Result[Tweet]:
        """
        Retrieves the timeline.
        Retrieves tweets from Home -> Following.

        Parameters
        ----------
        count : int, default=20
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
        >>> tweets = client.get_latest_timeline()
        >>> for tweet in tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...
        >>> more_tweets = tweets.next()  # Retrieve more tweets
        >>> for tweet in more_tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...
        """
        variables = {
            'count': count,
            'includePromotedContent': True,
            'latestControlAvailable': True,
            'requestContext': 'launch',
            'withCommunity': True,
            'seenTweetIds': seen_tweet_ids or [],
        }
        if cursor is not None:
            variables['cursor'] = cursor

        data = {
            'variables': variables,
            'queryId': get_query_id(Endpoint.HOME_LATEST_TIMELINE),
            'features': FEATURES,
        }
        response = self.http.post(
            Endpoint.HOME_LATEST_TIMELINE, json=data, headers=self._base_headers
        ).json()

        items = find_dict(response, 'entries')[0]
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
            next_cursor,
        )

    def favorite_tweet(self, tweet_id: str) -> Response:
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
        >>> client.favorite_tweet(tweet_id)

        See Also
        --------
        .unfavorite_tweet
        """
        data = {
            'variables': {'tweet_id': tweet_id},
            'queryId': get_query_id(Endpoint.FAVORITE_TWEET),
        }
        return self.http.post(Endpoint.FAVORITE_TWEET, json=data, headers=self._base_headers)

    def unfavorite_tweet(self, tweet_id: str) -> Response:
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
        >>> client.unfavorite_tweet(tweet_id)

        See Also
        --------
        .favorite_tweet
        """
        data = {
            'variables': {'tweet_id': tweet_id},
            'queryId': get_query_id(Endpoint.UNFAVORITE_TWEET),
        }
        return self.http.post(Endpoint.UNFAVORITE_TWEET, json=data, headers=self._base_headers)

    def retweet(self, tweet_id: str) -> Response:
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
        >>> client.retweet(tweet_id)

        See Also
        --------
        .delete_retweet
        """
        data = {
            'variables': {'tweet_id': tweet_id, 'dark_request': False},
            'queryId': get_query_id(Endpoint.CREATE_RETWEET),
        }
        return self.http.post(Endpoint.CREATE_RETWEET, json=data, headers=self._base_headers)

    def delete_retweet(self, tweet_id: str) -> Response:
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
        >>> client.delete_retweet(tweet_id)

        See Also
        --------
        .retweet
        """
        data = {
            'variables': {'source_tweet_id': tweet_id, 'dark_request': False},
            'queryId': get_query_id(Endpoint.DELETE_RETWEET),
        }
        return self.http.post(Endpoint.DELETE_RETWEET, json=data, headers=self._base_headers)

    def bookmark_tweet(self, tweet_id: str, folder_id: str | None = None) -> Response:
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
        >>> client.bookmark_tweet(tweet_id)
        """
        variables = {'tweet_id': tweet_id}
        if folder_id is None:
            endpoint = Endpoint.CREATE_BOOKMARK
        else:
            endpoint = Endpoint.BOOKMARK_TO_FOLDER
            variables['bookmark_collection_id'] = folder_id

        data = {'variables': variables, 'queryId': get_query_id(Endpoint.CREATE_BOOKMARK)}
        return self.http.post(endpoint, json=data, headers=self._base_headers)

    def delete_bookmark(self, tweet_id: str) -> Response:
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
        >>> client.delete_bookmark(tweet_id)

        See Also
        --------
        .bookmark_tweet
        """
        data = {
            'variables': {'tweet_id': tweet_id},
            'queryId': get_query_id(Endpoint.DELETE_BOOKMARK),
        }
        return self.http.post(Endpoint.DELETE_BOOKMARK, json=data, headers=self._base_headers)

    def get_bookmarks(
        self, count: int = 20, cursor: str | None = None, folder_id: str | None = None
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
        >>> bookmarks = client.get_bookmarks()
        >>> for bookmark in bookmarks:
        ...     print(bookmark)
        <Tweet id="...">
        <Tweet id="...">

        >>> more_bookmarks = bookmarks.next()  # To retrieve more bookmarks
        >>> for bookmark in more_bookmarks:
        ...     print(bookmark)
        <Tweet id="...">
        <Tweet id="...">
        """
        variables = {'count': count, 'includePromotedContent': True}
        if folder_id is None:
            endpoint = Endpoint.BOOKMARKS
            features = FEATURES | {'graphql_timeline_v2_bookmark_timeline': True}
        else:
            endpoint = Endpoint.BOOKMARK_FOLDER_TIMELINE
            variables['bookmark_collection_id'] = folder_id
            features = BOOKMARK_FOLDER_TIMELINE_FEATURES

        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({'variables': variables, 'features': features})
        response = self.http.get(endpoint, params=params, headers=self._base_headers).json()

        items_ = find_dict(response, 'entries')
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
            if not item['entryId'].startswith('tweet'):
                continue
            tweet = tweet_from_data(self, item)
            if tweet is None:
                continue
            results.append(tweet)

        return Result(
            results,
            partial(self.get_bookmarks, count, next_cursor, folder_id),
            next_cursor,
            fetch_previous_result,
            previous_cursor,
        )

    def delete_all_bookmarks(self) -> Response:
        """
        Deleted all bookmarks.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> client.delete_all_bookmarks()
        """
        data = {'variables': {}, 'queryId': get_query_id(Endpoint.BOOKMARKS_ALL_DELETE)}
        return self.http.post(Endpoint.BOOKMARKS_ALL_DELETE, json=data, headers=self._base_headers)

    def get_bookmark_folders(self, cursor: str | None = None) -> Result[BookmarkFolder]:
        """
        Retrieves bookmark folders.

        Returns
        -------
        Result[:class:`BookmarkFolder`]
            Result object containing a list of bookmark folders.

        Examples
        --------
        >>> folders = client.get_bookmark_folders()
        >>> print(folders)
        [<BookmarkFolder id="...">, ..., <BookmarkFolder id="...">]
        >>> more_folders = folders.next()  # Retrieve more folders
        """
        variables = {}
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({'variables': variables})
        response = self.http.get(
            Endpoint.BOOKMARK_FOLDERS, params=params, headers=self._base_headers
        ).json()

        slice = find_dict(response, 'bookmark_collections_slice')[0]
        results = []
        for item in slice['items']:
            results.append(BookmarkFolder(self, item))

        if 'next_cursor' in slice['slice_info']:
            next_cursor = slice['slice_info']['next_cursor']
            fetch_next_result = partial(self.get_bookmark_folders, next_cursor)
        else:
            next_cursor = None
            fetch_next_result = None

        return Result(results, fetch_next_result, next_cursor)

    def edit_bookmark_folder(self, folder_id: str, name: str) -> BookmarkFolder:
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
        >>> client.edit_bookmark_folder('123456789', 'MyFolder')
        """
        variables = {'bookmark_collection_id': folder_id, 'name': name}
        data = {'variables': variables, 'queryId': get_query_id(Endpoint.EDIT_BOOKMARK_FOLDER)}
        response = self.http.post(
            Endpoint.EDIT_BOOKMARK_FOLDER, json=data, headers=self._base_headers
        ).json()
        return BookmarkFolder(self, response['data']['bookmark_collection_update'])

    def delete_bookmark_folder(self, folder_id: str) -> Response:
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
        variables = {'bookmark_collection_id': folder_id}
        data = {'variables': variables, 'queryId': get_query_id(Endpoint.DELETE_BOOKMARK_FOLDER)}
        return self.http.post(
            Endpoint.DELETE_BOOKMARK_FOLDER, json=data, headers=self._base_headers
        )

    def create_bookmark_folder(self, name: str) -> BookmarkFolder:
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
        variables = {'name': name}
        data = {'variables': variables, 'queryId': get_query_id(Endpoint.CREATE_BOOKMARK_FOLDER)}
        response = self.http.post(
            Endpoint.CREATE_BOOKMARK_FOLDER, json=data, headers=self._base_headers
        ).json()
        return BookmarkFolder(self, response['data']['bookmark_collection_create'])

    def follow_user(self, user_id: str) -> Response:
        """
        Follows a user.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user to follow.

        Returns
        -------
        :class:`httpx.Response:class:`
            Response returned from twitter api.

        Examples
        --------
        >>> user_id = '...'
        >>> client.follow_user(user_id)

        See Also
        --------
        .unfollow_user
        """
        data = urlencode(
            {
                'include_profile_interstitial_type': 1,
                'include_blocking': 1,
                'include_blocked_by': 1,
                'include_followed_by': 1,
                'include_want_retweets': 1,
                'include_mute_edge': 1,
                'include_can_dm': 1,
                'include_can_media_tag': 1,
                'include_ext_is_blue_verified': 1,
                'include_ext_verified_type': 1,
                'include_ext_profile_image_shape': 1,
                'skip_status': 1,
                'user_id': user_id,
            }
        )
        headers = self._base_headers | {'content-type': 'application/x-www-form-urlencoded'}
        return self.http.post(Endpoint.CREATE_FRIENDSHIPS, data=data, headers=headers)

    def unfollow_user(self, user_id: str) -> Response:
        """
        Unfollows a user.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user to unfollow.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> user_id = '...'
        >>> client.unfollow_user(user_id)

        See Also
        --------
        .follow_user
        """
        data = urlencode(
            {
                'include_profile_interstitial_type': 1,
                'include_blocking': 1,
                'include_blocked_by': 1,
                'include_followed_by': 1,
                'include_want_retweets': 1,
                'include_mute_edge': 1,
                'include_can_dm': 1,
                'include_can_media_tag': 1,
                'include_ext_is_blue_verified': 1,
                'include_ext_verified_type': 1,
                'include_ext_profile_image_shape': 1,
                'skip_status': 1,
                'user_id': user_id,
            }
        )
        headers = self._base_headers | {'content-type': 'application/x-www-form-urlencoded'}
        return self.http.post(Endpoint.DESTROY_FRIENDSHIPS, data=data, headers=headers)

    def block_user(self, user_id: str) -> Response:
        """
        Blocks a user.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user to block.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        See Also
        --------
        .unblock_user
        """
        data = urlencode({'user_id': user_id})
        headers = self._base_headers
        headers['content-type'] = 'application/x-www-form-urlencoded'
        return self.http.post(Endpoint.BLOCK_USER, data=data, headers=headers)

    def unblock_user(self, user_id: str) -> Response:
        """
        Unblocks a user.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user to unblock.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        See Also
        --------
        .block_user
        """
        data = urlencode({'user_id': user_id})
        headers = self._base_headers
        headers['content-type'] = 'application/x-www-form-urlencoded'
        return self.http.post(Endpoint.UNBLOCK_USER, data=data, headers=headers)

    def mute_user(self, user_id: str) -> Response:
        """
        Mutes a user.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user to mute.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        See Also
        --------
        .unmute_user
        """
        data = urlencode({'user_id': user_id})
        headers = self._base_headers
        headers['content-type'] = 'application/x-www-form-urlencoded'
        return self.http.post(Endpoint.MUTE_USER, data=data, headers=headers)

    def unmute_user(self, user_id: str) -> Response:
        """
        Unmutes a user.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user to unmute.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        See Also
        --------
        .mute_user
        """
        data = urlencode({'user_id': user_id})
        headers = self._base_headers
        headers['content-type'] = 'application/x-www-form-urlencoded'
        return self.http.post(Endpoint.UNMUTE_USER, data=data, headers=headers)

    def get_trends(
        self,
        category: Literal['trending', 'for-you', 'news', 'sports', 'entertainment'],
        count: int = 20,
        retry: bool = True,
        additional_request_params: dict | None = None,
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
        >>> trends = client.get_trends('trending')
        >>> for trend in trends:
        ...     print(trend)
        <Trend name="...">
        <Trend name="...">
        ...
        """
        category = category.lower()
        if category in ['news', 'sports', 'entertainment']:
            category += '_unified'
        params = {'count': count, 'include_page_configuration': True, 'initial_tab_id': category}
        if additional_request_params is not None:
            params |= additional_request_params
        response = self.http.get(Endpoint.TREND, params=params, headers=self._base_headers).json()

        entry_id_prefix = 'trends' if category == 'trending' else 'Guide'
        entries = [
            i for i in find_dict(response, 'entries')[0] if i['entryId'].startswith(entry_id_prefix)
        ]

        if not entries:
            if not retry:
                return []
            # Recall the method again, as the trend information
            # may not be returned due to a Twitter error.
            return self.get_trends(category, count, retry, additional_request_params)

        items = entries[-1]['content']['timelineModule']['items']

        results = []
        for item in items:
            trend_info = item['item']['content']['trend']
            results.append(Trend(self, trend_info))

        return results

    def _get_user_friendship(
        self, user_id: str, count: int, endpoint: str, cursor: str | None
    ) -> Result[User]:
        """
        Base function to get friendship.
        """
        variables = {'userId': user_id, 'count': count, 'includePromotedContent': False}
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({'variables': variables, 'features': FEATURES})
        response = self.http.get(endpoint, params=params, headers=self._base_headers).json()

        items = find_dict(response, 'entries')[0]
        results = []
        for item in items:
            entry_id = item['entryId']
            if entry_id.startswith('user'):
                user_info = find_dict(item, 'result')
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
            partial(self._get_user_friendship, user_id, count, endpoint, next_cursor),
            next_cursor,
        )

    def get_user_followers(
        self, user_id: str, count: int = 20, cursor: str | None = None
    ) -> Result[User]:
        """
        Retrieves a list of followers for a given user.

        Parameters
        ----------
        user_id : :class:`str`
            The ID of the user for whom to retrieve followers.
        count : :class:`int`, default=20
            The number of followers to retrieve.

        Returns
        -------
        Result[:class:`User`]
            A list of User objects representing the followers.
        """
        return self._get_user_friendship(user_id, count, Endpoint.FOLLOWERS, cursor)

    def get_user_verified_followers(
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
        return self._get_user_friendship(user_id, count, Endpoint.BLUE_VERIFIED_FOLLOWERS, cursor)

    def get_user_followers_you_know(
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
        return self._get_user_friendship(user_id, count, Endpoint.FOLLOWERS_YOU_KNOW, cursor)

    def get_user_following(
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
        return self._get_user_friendship(user_id, count, Endpoint.FOLLOWING, cursor)

    def get_user_subscriptions(
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
        return self._get_user_friendship(user_id, count, Endpoint.SUBSCRIPTIONS, cursor)

    def _send_dm(
        self, conversation_id: str, text: str, media_id: str | None, reply_to: str | None
    ) -> dict:
        """
        Base function to send dm.
        """
        data = {
            'cards_platform': 'Web-12',
            'conversation_id': conversation_id,
            'dm_users': False,
            'include_cards': 1,
            'include_quote_count': True,
            'recipient_ids': False,
            'text': text,
        }
        if media_id is not None:
            data['media_id'] = media_id
        if reply_to is not None:
            data['reply_to_dm_id'] = reply_to

        return self.http.post(Endpoint.SEND_DM, json=data, headers=self._base_headers).json()

    def _get_dm_history(self, conversation_id: str, max_id: str | None = None) -> dict:
        """
        Base function to get dm history.
        """
        params = {'context': 'FETCH_DM_CONVERSATION_HISTORY'}
        if max_id is not None:
            params['max_id'] = max_id

        return self.http.get(
            Endpoint.CONVERSASION.format(conversation_id), params=params, headers=self._base_headers
        ).json()

    def send_dm(
        self, user_id: str, text: str, media_id: str | None = None, reply_to: str | None = None
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
        >>> media_id = client.upload_media('image.png')
        >>> message = client.send_dm(user_id, 'text', media_id)
        >>> print(message)
        <Message id='...'>

        See Also
        --------
        .upload_media
        .delete_dm
        """
        response = self._send_dm(f'{user_id}-{self.user_id()}', text, media_id, reply_to)

        message_data = find_dict(response, 'message_data')[0]
        users = list(response['users'].values())
        return Message(
            self,
            message_data,
            users[0]['id_str'],
            users[1]['id_str'] if len(users) == 2 else users[0]['id_str'],
        )

    def add_reaction_to_message(
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
        >>> conversation_id = f'00000001-{client.user_id()}'
        >>> client.add_reaction_to_message(message_id, conversation_id, 'Emoji here')
        """
        variables = {
            'messageId': message_id,
            'conversationId': conversation_id,
            'reactionTypes': ['Emoji'],
            'emojiReactions': [emoji],
        }
        data = {'variables': variables, 'queryId': get_query_id(Endpoint.MESSAGE_ADD_REACTION)}
        return self.http.post(Endpoint.MESSAGE_ADD_REACTION, json=data, headers=self._base_headers)

    def remove_reaction_from_message(
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
        >>> conversation_id = f'00000001-{client.user_id()}'
        >>> client.remove_reaction_from_message(message_id, conversation_id, 'Emoji here')
        """
        variables = {
            'conversationId': conversation_id,
            'messageId': message_id,
            'reactionTypes': ['Emoji'],
            'emojiReactions': [emoji],
        }
        data = {'variables': variables, 'queryId': get_query_id(Endpoint.MESSAGE_REMOVE_REACTION)}
        return self.http.post(
            Endpoint.MESSAGE_REMOVE_REACTION, json=data, headers=self._base_headers
        )

    def delete_dm(self, message_id: str) -> Response:
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
        >>> client.delete_dm('0000000000')
        """

        data = {'variables': {'messageId': message_id}, 'queryId': get_query_id(Endpoint.DELETE_DM)}
        return self.http.post(Endpoint.DELETE_DM, json=data, headers=self._base_headers)

    def get_dm_history(self, user_id: str, max_id: str | None = None) -> Result[Message]:
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
        >>> messages = client.get_dm_history('0000000000')
        >>> for message in messages:
        >>>     print(message)
        <Message id="...">
        <Message id="...">
        ...
        ...

        >>> more_messages = messages.next()  # Retrieve more messages
        >>> for message in more_messages:
        >>>     print(message)
        <Message id="...">
        <Message id="...">
        ...
        ...
        """
        response = self._get_dm_history(f'{user_id}-{self.user_id()}', max_id)

        items = response['conversation_timeline']['entries']
        messages = []
        for item in items:
            message_info = item['message']['message_data']
            messages.append(
                Message(self, message_info, message_info['sender_id'], message_info['recipient_id'])
            )
        return Result(
            messages, partial(self.get_dm_history, user_id, messages[-1].id), messages[-1].id
        )

    def send_dm_to_group(
        self, group_id: str, text: str, media_id: str | None = None, reply_to: str | None = None
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
        >>> media_id = client.upload_media('image.png')
        >>> message = client.send_dm_to_group(group_id, 'text', media_id)
        >>> print(message)
        <GroupMessage id='...'>

        See Also
        --------
        .upload_media
        .delete_dm
        """
        response = self._send_dm(group_id, text, media_id, reply_to)

        message_data = find_dict(response, 'message_data')[0]
        users = list(response['users'].values())
        return GroupMessage(self, message_data, users[0]['id_str'], group_id)

    def get_group_dm_history(
        self, group_id: str, max_id: str | None = None
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
        >>> messages = client.get_group_dm_history('0000000000')
        >>> for message in messages:
        >>>     print(message)
        <GroupMessage id="...">
        <GroupMessage id="...">
        ...
        ...

        >>> more_messages = messages.next()  # Retrieve more messages
        >>> for message in more_messages:
        >>>     print(message)
        <GroupMessage id="...">
        <GroupMessage id="...">
        ...
        ...
        """
        response = self._get_dm_history(group_id, max_id)

        items = response['conversation_timeline']['entries']
        messages = []
        for item in items:
            if 'message' not in item:
                continue
            message_info = item['message']['message_data']
            messages.append(GroupMessage(self, message_info, message_info['sender_id'], group_id))
        return Result(
            messages, partial(self.get_group_dm_history, group_id, messages[-1].id), messages[-1].id
        )

    def get_group(self, group_id: str) -> Group:
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
        params = {
            'context': 'FETCH_DM_CONVERSATION_HISTORY',
            'include_conversation_info': True,
        }
        response = self.http.get(
            Endpoint.CONVERSASION.format(group_id), params=params, headers=self._base_headers
        ).json()
        return Group(self, group_id, response)

    def add_members_to_group(self, group_id: str, user_ids: list[str]) -> Response:
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
        >>> client.add_members_to_group(group_id, members)
        """
        data = {
            'variables': {'addedParticipants': user_ids, 'conversationId': group_id},
            'queryId': get_query_id(Endpoint.ADD_MEMBER_TO_GROUP),
        }
        return self.http.post(Endpoint.ADD_MEMBER_TO_GROUP, json=data, headers=self._base_headers)

    def change_group_name(self, group_id: str, name: str) -> Response:
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
        data = urlencode({'name': name})
        headers = self._base_headers
        headers['content-type'] = 'application/x-www-form-urlencoded'
        return self.http.post(
            Endpoint.CHANGE_GROUP_NAME.format(group_id), data=data, headers=headers
        )

    def create_list(self, name: str, description: str = '', is_private: bool = False) -> List:
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
        list
            The created list.

        Examples
        --------
        >>> list = client.create_list('list name', 'list description', is_private=True)
        >>> print(list)
        <List id="...">
        """
        variables = {'isPrivate': is_private, 'name': name, 'description': description}
        data = {
            'variables': variables,
            'features': LIST_FEATURES,
            'queryId': get_query_id(Endpoint.CREATE_LIST),
        }
        response = self.http.post(
            Endpoint.CREATE_LIST, json=data, headers=self._base_headers
        ).json()
        list_info = find_dict(response, 'list')[0]
        return List(self, list_info)

    def edit_list_banner(self, list_id: str, media_id: str) -> Response:
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
        >>> media_id = client.upload_media('image.png')
        >>> client.edit_list_banner(list_id, media_id)
        """
        variables = {'listId': list_id, 'mediaId': media_id}
        data = {
            'variables': variables,
            'features': LIST_FEATURES,
            'queryId': get_query_id(Endpoint.EDIT_LIST_BANNER),
        }
        return self.http.post(Endpoint.EDIT_LIST_BANNER, json=data, headers=self._base_headers)

    def delete_list_banner(self, list_id: str) -> Response:
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
        data = {
            'variables': {'listId': list_id},
            'features': LIST_FEATURES,
            'queryId': get_query_id(Endpoint.DELETE_LIST_BANNER),
        }
        return self.http.post(Endpoint.DELETE_LIST_BANNER, json=data, headers=self._base_headers)

    def edit_list(
        self,
        list_id: str,
        name: str | None = None,
        description: str | None = None,
        is_private: bool | None = None,
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
        list
            The updated Twitter list.

        Examples
        --------
        >>> client.edit_list('new name', 'new description', True)
        """
        variables = {'listId': list_id}
        if name is not None:
            variables['name'] = name
        if description is not None:
            variables['description'] = description
        if is_private is not None:
            variables['isPrivate'] = is_private
        data = {
            'variables': variables,
            'features': LIST_FEATURES,
            'queryId': get_query_id(Endpoint.UPDATE_LIST),
        }
        response = self.http.post(
            Endpoint.UPDATE_LIST, json=data, headers=self._base_headers
        ).json()
        list_info = find_dict(response, 'list')[0]
        return List(self, list_info)

    def add_list_member(self, list_id: str, user_id: str) -> Response:
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
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> client.add_list_member('list id', 'user id')
        """
        variables = {'listId': list_id, 'userId': user_id}
        data = {
            'variables': variables,
            'features': LIST_FEATURES,
            'queryId': get_query_id(Endpoint.LIST_ADD_MEMBER),
        }
        return self.http.post(Endpoint.LIST_ADD_MEMBER, json=data, headers=self._base_headers)

    def remove_list_member(self, list_id: str, user_id: str) -> Response:
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
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> client.remove_list_member('list id', 'user id')
        """
        variables = {'listId': list_id, 'userId': user_id}
        data = {
            'variables': variables,
            'features': LIST_FEATURES,
            'queryId': get_query_id(Endpoint.LIST_REMOVE_MEMBER),
        }
        return self.http.post(Endpoint.LIST_REMOVE_MEMBER, json=data, headers=self._base_headers)

    def get_lists(self, count: int = 100, cursor: str = None) -> Result[List]:
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
        variables = {'count': count}
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({'variables': variables, 'features': FEATURES})
        response = self.http.get(
            Endpoint.LIST_MANAGEMENT, params=params, headers=self._base_headers
        ).json()

        entries = find_dict(response, 'entries')[0]
        items = find_dict(entries, 'items')

        if len(items) < 2:
            return Result([])

        lists = []
        for list in items[1]:
            lists.append(List(self, list['item']['itemContent']['list']))

        next_cursor = entries[-1]['content']['value']

        return Result(lists, partial(self.get_lists, count, next_cursor), next_cursor)

    def get_list(self, list_id: str) -> List:
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
        params = flatten_params({'variables': {'listId': list_id}, 'features': LIST_FEATURES})
        response = self.http.get(
            Endpoint.LIST_BY_REST_ID, params=params, headers=self._base_headers
        ).json()
        list_info = find_dict(response, 'list')[0]
        return List(self, list_info)

    def get_list_tweets(
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
        >>> tweets = client.get_list_tweets('list id')
        >>> for tweet in tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...

        >>> more_tweets = tweets.next()  # Retrieve more tweets
        >>> for tweet in more_tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...
        """
        variables = {'listId': list_id, 'count': count}
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({'variables': variables, 'features': FEATURES})
        response = self.http.get(
            Endpoint.LIST_LATEST_TWEETS, params=params, headers=self._base_headers
        ).json()

        items = find_dict(response, 'entries')[0]
        next_cursor = items[-1]['content']['value']

        results = []
        for item in items:
            if not item['entryId'].startswith('tweet'):
                continue

            tweet = tweet_from_data(self, item)
            if tweet is not None:
                results.append(tweet)

        return Result(
            results, partial(self.get_list_tweets, list_id, count, next_cursor), next_cursor
        )

    def _get_list_users(self, endpoint: str, list_id: str, count: int, cursor: str) -> Result[User]:
        """
        Base function to retrieve the users associated with a list.
        """
        variables = {
            'listId': list_id,
            'count': count,
        }
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({'variables': variables, 'features': FEATURES})
        response = self.http.get(endpoint, params=params, headers=self._base_headers).json()

        items = find_dict(response, 'entries')[0]
        results = []
        for item in items:
            entry_id = item['entryId']
            if entry_id.startswith('user'):
                user_info = find_dict(item, 'result')[0]
                results.append(User(self, user_info))
            elif entry_id.startswith('cursor-bottom'):
                next_cursor = item['content']['value']
                break

        return Result(
            results,
            partial(self._get_list_users, endpoint, list_id, count, next_cursor),
            next_cursor,
        )

    def get_list_members(
        self, list_id: str, count: int = 20, cursor: str | None = None
    ) -> Result[User]:
        """Retrieves members of a list.

        Parameters
        ----------
        list_id : :class:`str`
            List ID.
        count : :class:`int`, default=20
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
        return self._get_list_users(Endpoint.LIST_MEMBERS, list_id, count, cursor)

    def get_list_subscribers(
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
        return self._get_list_users(Endpoint.LIST_SUBSCRIBERS, list_id, count, cursor)

    def search_list(self, query: str, count: int = 20, cursor: str | None = None) -> Result[List]:
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
        >>> lists = client.search_list('query')
        >>> for list in lists:
        ...     print(list)
        <List id="...">
        <List id="...">
        ...

        >>> more_lists = lists.next()  # Retrieve more lists
        """
        response = self._search(query, 'Lists', count, cursor)
        entries = find_dict(response, 'entries')[0]

        if cursor is None:
            items = entries[0]['content']['items']
        else:
            items = find_dict(response, 'moduleItems')[0]

        lists = []
        for item in items:
            lists.append(List(self, item['item']['itemContent']['list']))
        next_cursor = entries[-1]['content']['value']

        return Result(lists, partial(self.search_list, query, count, next_cursor), next_cursor)

    def get_notifications(
        self,
        type: Literal['All', 'Verified', 'Mentions'],
        count: int = 40,
        cursor: str | None = None,
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
        >>> notifications = client.get_notifications('All')
        >>> for notification in notifications:
        ...     print(notification)
        <Notification id="...">
        <Notification id="...">
        ...
        ...

        >>> # Retrieve more notifications
        >>> more_notifications = notifications.next()
        """
        type = type.capitalize()

        endpoint = {
            'All': Endpoint.NOTIFICATIONS_ALL,
            'Verified': Endpoint.NOTIFICATIONS_VERIFIED,
            'Mentions': Endpoint.NOTIFICATIONS_MENTIONES,
        }[type]

        params = {'count': count}
        if cursor is not None:
            params['cursor'] = cursor

        response = self.http.get(endpoint, params=params, headers=self._base_headers).json()

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

            from_users = user_actions['fromUsers']
            if from_users and 'user' in from_users[0]:
                user_id = from_users[0]['user']['id']
                user = users[user_id]
            else:
                user = None

            notifications.append(Notification(self, notification, tweet, user))

        entries = find_dict(response, 'entries')[0]
        cursor_bottom_entry = [i for i in entries if i['entryId'].startswith('cursor-bottom')]
        if cursor_bottom_entry:
            next_cursor = find_dict(cursor_bottom_entry[0], 'value')[0]
        else:
            next_cursor = None

        return Result(
            notifications, partial(self.get_notifications, type, count, next_cursor), next_cursor
        )

    def search_community(self, query: str, cursor: str | None = None) -> Result[Community]:
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
        >>> communities = client.search_communities('query')
        >>> for community in communities:
        ...     print(community)
        <Community id="...">
        <Community id="...">
        ...

        >>> more_communities = communities.next()  # Retrieve more communities
        """
        variables = {
            'query': query,
        }
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({'variables': variables})
        response = self.http.get(
            Endpoint.SEARCH_COMMUNITY, params=params, headers=self._base_headers
        ).json()

        items = find_dict(response, 'items_results')[0]
        communities = []
        for item in items:
            communities.append(Community(self, item['result']))
        next_cursor_ = find_dict(response, 'next_cursor')
        next_cursor = next_cursor_[0] if next_cursor_ else None
        if next_cursor is None:
            fetch_next_result = None
        else:
            fetch_next_result = partial(self.search_community, query, next_cursor)
        return Result(communities, fetch_next_result, next_cursor)

    def get_community(self, community_id: str) -> Community:
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
        params = flatten_params(
            {
                'variables': {'communityId': community_id},
                'features': {
                    'c9s_list_members_action_api_enabled': False,
                    'c9s_superc9s_indication_enabled': False,
                },
            }
        )
        response = self.http.get(
            Endpoint.GET_COMMUNITY, params=params, headers=self._base_headers
        ).json()
        community_data = find_dict(response, 'result')[0]
        return Community(self, community_data)

    def get_community_tweets(
        self,
        community_id: str,
        tweet_type: Literal['Top', 'Latest', 'Media'],
        count: int = 40,
        cursor: str | None = None,
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
        >>> tweets = client.get_community_tweets(community_id, 'Latest')
        >>> for tweet in tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        >>> more_tweets = tweets.next()  # Retrieve more tweets
        """
        tweet_type = tweet_type.capitalize()

        variables = {'communityId': community_id, 'count': count, 'withCommunity': True}

        if tweet_type == 'Media':
            endpoint = Endpoint.COMMUNITY_MEDIA
        else:
            endpoint = Endpoint.COMMUNITY_TWEETS
            variables['rankingMode'] = {'Top': 'Relevance', 'Latest': 'Recency'}[tweet_type]

        if cursor is not None:
            variables['cursor'] = cursor

        params = flatten_params({'variables': variables, 'features': COMMUNITY_TWEETS_FEATURES})
        response = self.http.get(endpoint, params=params, headers=self._base_headers).json()

        entries = find_dict(response, 'entries')[0]
        if tweet_type == 'Media':
            if cursor is None:
                items = entries[0]['content']['items']
                next_cursor = entries[-1]['content']['value']
                previous_cursor = entries[-2]['content']['value']
            else:
                items = find_dict(response, 'moduleItems')[0]
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
            previous_cursor,
        )

    def get_communities_timeline(self, count: int = 20, cursor: str | None = None) -> Result[Tweet]:
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
        >>> tweets = client.get_communities_timeline()
        >>> for tweet in tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        >>> more_tweets = tweets.next()  # Retrieve more tweets
        """
        variables = {'count': count, 'withCommunity': True}
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({'variables': variables, 'features': COMMUNITY_TWEETS_FEATURES})
        response = self.http.get(
            Endpoint.COMMUNITIES_TIMELINE, params=params, headers=self._base_headers
        ).json()
        items = find_dict(response, 'entries')[0]
        tweets = []
        for item in items:
            if not item['entryId'].startswith('tweet'):
                continue
            tweet = tweet_from_data(self, item)
            tweet_data = find_dict(item, 'result')[0]
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
            previous_cursor,
        )

    def join_community(self, community_id: str) -> Community:
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
        data = {
            'variables': {'communityId': community_id},
            'features': JOIN_COMMUNITY_FEATURES,
            'queryId': get_query_id(Endpoint.JOIN_COMMUNITY),
        }
        response = self.http.post(
            Endpoint.JOIN_COMMUNITY, json=data, headers=self._base_headers
        ).json()
        community_data = response['data']['community_join']
        community_data['rest_id'] = community_data['id_str']
        return Community(self, community_data)

    def leave_community(self, community_id: str) -> Community:
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
        data = {
            'variables': {'communityId': community_id},
            'features': JOIN_COMMUNITY_FEATURES,
            'queryId': get_query_id(Endpoint.LEAVE_COMMUNITY),
        }
        response = self.http.post(
            Endpoint.LEAVE_COMMUNITY, json=data, headers=self._base_headers
        ).json()
        community_data = response['data']['community_leave']
        community_data['rest_id'] = community_data['id_str']
        return Community(self, community_data)

    def request_to_join_community(self, community_id: str, answer: str | None = None) -> Community:
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
        data = {
            'variables': {'communityId': community_id, 'answer': '' if answer is None else answer},
            'features': JOIN_COMMUNITY_FEATURES,
            'queryId': get_query_id(Endpoint.REQUEST_TO_JOIN_COMMUNITY),
        }
        response = self.http.post(
            Endpoint.REQUEST_TO_JOIN_COMMUNITY, json=data, headers=self._base_headers
        ).json()
        community_data = find_dict(response, 'result')[0]
        community_data['rest_id'] = community_data['id_str']
        return Community(self, community_data)

    def _get_community_users(
        self, endpoint: str, community_id: str, count: int, cursor: str | None
    ):
        """
        Base function to retrieve community users.
        """
        variables = {'communityId': community_id, 'count': count}
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params(
            {
                'variables': variables,
                'features': {'responsive_web_graphql_timeline_navigation_enabled': True},
            }
        )
        response = self.http.get(endpoint, params=params, headers=self._base_headers).json()

        items = find_dict(response, 'items_results')[0]
        users = []
        for item in items:
            if not 'result' in item:
                continue
            if item['result'].get('__typename') != 'User':
                continue
            users.append(CommunityMember(self, item['result']))

        next_cursor_ = find_dict(response, 'next_cursor')
        next_cursor = next_cursor_[0] if next_cursor_ else None

        if next_cursor is None:
            fetch_next_result = None
        else:
            fetch_next_result = partial(
                self._get_community_users, endpoint, community_id, count, next_cursor
            )
        return Result(users, fetch_next_result, next_cursor)

    def get_community_members(
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
        return self._get_community_users(Endpoint.COMMUNITY_MEMBERS, community_id, count, cursor)

    def get_community_moderators(
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
        return self._get_community_users(Endpoint.COMMUNITY_MODERATORS, community_id, count, cursor)

    def search_community_tweet(
        self, community_id: str, query: str, count: int = 20, cursor: str | None = None
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
        variables = {
            'count': count,
            'query': query,
            'communityId': community_id,
            'includePromotedContent': False,
            'withBirdwatchNotes': True,
            'withVoice': False,
            'isListMemberTargetUserId': '0',
            'withCommunity': False,
            'withSafetyModeUserFields': True,
        }
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({'variables': variables, 'features': COMMUNITY_TWEETS_FEATURES})
        response = self.http.get(
            Endpoint.SEARCH_COMMUNITY_TWEET, params=params, headers=self._base_headers
        ).json()

        items = find_dict(response, 'entries')[0]
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
