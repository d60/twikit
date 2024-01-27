"""
Python Twitter API
==================

A Python library for interacting with the Twitter API.
"""

from __future__ import annotations

import io
import json
import os
import pickle
from typing import Literal
from urllib import parse

import requests

from tweet import Tweet
from user import User
from utils import (
    FEATURES,
    TOKEN,
    USER_FEATURES,
    Endpoint,
    Result,
    find_dict
)


class Client:
    """
    Examples
    --------
    >>> client = Client(token='TOKEN', language='en-US')

    >>> # Specify two out of three: username, email, phone_number
    >>> client.login(
    ...     username='example_user',
    ...     email='email@example.com',
    ...     password='00000000'
    ... )

    >>> # Save cookies to a file:
    >>> client.save_cookies('cookies.pkl')

    >>> # Skip the login step by loading saved cookies
    >>> client.load_cookies('cookies.pkl')
    """

    def __init__(self, language: str) -> None:
        self._token = TOKEN
        self.language = language
        self._session = requests.Session()

    def _get_guest_token(self) -> str:
        response = self._session.post(
            Endpoint.GUEST_TOKEN,
            headers=self.base_headers,
            data={}
        ).json()
        guest_token = response['guest_token']
        return guest_token

    def save_cookies(self, path: str) -> None:
        """
        Saves cookies to file.
        """
        with open(path, 'wb') as f:
            pickle.dump(self._session.cookies, f)

    def load_cookies(self, path: str) -> None:
        """
        Loads cookies from a file.
        """
        with open(path, 'rb') as f:
            self._session.cookies.update(pickle.load(f))

    @property
    def base_headers(self) -> dict[str, str]:
        """
        Base headers for Twitter API requests.
        """
        return {
            'authorization': f'Bearer {self._token}',
            'content-type': 'application/json',
            'Accept-Language': self.language,
            'X-Twitter-Client-Language': self.language,
            'Referer': 'https://twitter.com/',
            'X-Csrf-Token': self._get_csrf_token()
        }

    def _get_csrf_token(self) -> str:
        """
        Retrieves the Cross-Site Request Forgery (CSRF) token from the
        current session's cookies.

        Returns
        -------
        str
            The CSRF token as a string.
        """
        return self._session.cookies.get_dict().get('ct0')

    def login(
        self,
        *,
        username: str = None,
        email: str = None,
        phone_number: str = None,
        password: str,
    ) -> None:
        """
        Logs in a user using the specified credentials.

        >>> client.login(
        ...     guest_token='00000000000',
        ...     username='example_user',
        ...     email='email@example.com'
        ... )

        Parameters
        ----------
        username : str, optional
            The username of the user.
        email : str, optional
            The email address of the user.
        phone_number : str, optional
            The phone number of the user.
        password : str
            The password associated with the user account.
        """
        login_info = [
            i for i in (username, email, phone_number)
            if i is not None
        ]
        guest_token = self._get_guest_token()
        headers = self.base_headers | {
            'x-guest-token': guest_token
        }

        def _execute_task(
            flow_token: str = None,
            subtask_input: dict = None,
            flow_name: str = None
        ) -> dict:
            url = Endpoint.TASK
            if flow_name is not None:
                url += f'?flow_name={flow_name}'

            data = {}
            if flow_token is not None:
                data['flow_token'] = flow_token
            if subtask_input is not None:
                data['subtask_inputs'] = [subtask_input]

            response = self._session.post(
                url, data=json.dumps(data), headers=headers
            ).json()
            return response

        flow_token = _execute_task(flow_name='login')['flow_token']
        flow_token = _execute_task(flow_token)['flow_token']
        response = _execute_task(
            flow_token,
            {
                'subtask_id': 'LoginEnterUserIdentifierSSO',
                'settings_list': {
                    'setting_responses': [
                        {
                            'key': 'user_identifier',
                            'response_data': {
                                'text_data': {'result': login_info[0]}
                            }
                        }
                    ],
                    'link': 'next_link'
                }
            }
        )
        flow_token = response['flow_token']
        task_id = response['subtasks'][0]['subtask_id']

        if task_id == 'LoginEnterAlternateIdentifierSubtask':
            response = _execute_task(
                flow_token,
                {
                    'subtask_id': 'LoginEnterAlternateIdentifierSubtask',
                    'enter_text': {
                        'text': login_info[1],
                        'link': 'next_link'
                    }
                }
            )
            flow_token = response['flow_token']

        response = _execute_task(
            flow_token,
            {
                'subtask_id': 'LoginEnterPassword',
                'enter_password': {
                    'password': password,
                    'link': 'next_link'
                }
            }
        )
        flow_token = response['flow_token']

        _execute_task(
            flow_token,
            {
                'subtask_id': 'AccountDuplicationCheck',
                'check_logged_in_account': {
                    'link': 'AccountDuplicationCheck_false'
                }
            },
        )

    def _search(
        self,
        query: str,
        product: str,
        count: int,
        cursor: str
    ):
        """
        Base search function.
        """
        variables = {
            'rawQuery': query,
            'count': count,
            'querySource': 'typed_query',
            'product': product
        }
        if cursor is not None:
            variables['cursor'] = cursor
        params = {
            'variables': json.dumps(variables),
            'features': json.dumps(FEATURES)
        }
        response = self._session.get(
            Endpoint.SEARCH_TIMELINE,
            params=params,
            headers=self.base_headers
        ).json()

        return response

    def search_tweet(
        self,
        query: str,
        product: Literal['Top', 'Latest', 'Media'],
        count: int = 20,
        cursor: str = None
    ) -> Result[Tweet]:
        """
        Searches for tweets based on the specified query and product type.

        Parameters
        ----------
        query : str
            The search query.
        product : {'Top', 'Latest', 'Media'}
            The type of tweets to retrieve.
        count : int, default=20
            The number of tweets to retrieve, between 1 and 20.
        cursor : str, optional
            Token to retrieve more tweets.

        Returns
        -------
        Tweet
            An instance of the `Tweet` class containing the search results.

        Examples
        --------
        >>> tweets = client.search_tweet('query', 'Top')
        >>> for tweet in tweets:
        ...    print(tweet)
        <Tweet id="tweet_1">
        <Tweet id="tweet_2">
        ...
        ...

        >>> more_tweets = tweets.next  # Retrieve more tweets
        >>> for tweet in more_tweets:
        ...     print(tweet)
        <Tweet id="more_tweet_1">
        <Tweet id="more_tweet_2">
        ...
        ...
        """
        product = product.capitalize()

        response = self._search(query, product, count, cursor)
        instructions = find_dict(response, 'instructions')[0]

        if cursor is None and product == 'Media':
            items = instructions[-1]['entries'][0]['content']['items']
            next_cursor = instructions[-1]['entries'][-1]['content']['value']
        elif cursor is None:
            items = instructions[-1]['entries']
            next_cursor = items[-1]['content']['value']
        elif product == 'Media':
            items = instructions[0]['moduleItems']
            next_cursor = instructions[1]['entries'][1]['content']['value']
        else:
            items = instructions[0]['entries']
            next_cursor = instructions[-1]['entry']['content']['value']

        tweets = []
        for item in items:
            if product != 'Media' and 'itemContent' not in item['content']:
                continue
            tweet_info = find_dict(item, 'result')[0]
            if 'tweet' in tweet_info:
                tweet_info = tweet_info['tweet']
            user_info = tweet_info['core']['user_results']['result']
            tweets.append(Tweet(self, tweet_info, User(self, user_info)))

        return Result(
            tweets,
            lambda:self.search_tweet(query, product, count, next_cursor),
            next_cursor
        )

    def upload_media(self, source: str | bytes, index: int) -> int:
        """
        Uploads media to twitter.

        Parameters
        ----------
        media_path : str | bytes
            The file path or binary data of the media to be uploaded.
        index : int
            The index of the media segment being uploaded.
            Should start from 0 and increment by 1 for each subsequent upload.

        Returns
        -------
        int
            The media ID of the uploaded media.

        Examples
        --------
        Upload media files in sequence, starting from index 0.

        >>> media_id_1 = client._upload_media('media1.jpg', index=0)
        >>> media_id_2 = client._upload_media('media2.jpg', index=1)
        >>> media_id_3 = client._upload_media('media3.jpg', index=2)
        """
        if isinstance(source, str):
            # If the source is a path
            img_size = os.path.getsize(source)
            binary_stream = open(source, 'rb')
        elif isinstance(source, bytes):
            # If the source is bytes
            img_size = len(source)
            binary_stream = io.BytesIO(source)

        # ============ INIT =============
        params = {
            'command': 'INIT',
            'total_bytes': img_size,
        }
        response = self._session.post(
            Endpoint.UPLOAD_MEDIA,
            params=params,
            headers=self.base_headers
        ).json()
        media_id = response['media_id']
        # =========== APPEND ============
        params = {
            'command': 'APPEND',
            'media_id': media_id,
            'segment_index': index,
        }
        headers = self.base_headers
        headers.pop('content-type')
        files = {
            'media': (
                'blob',
                binary_stream,
                'application/octet-stream',
            )
        }
        response = self._session.post(
            Endpoint.UPLOAD_MEDIA,
            params=params,
            headers=headers,
            files=files
        )
        # ========== FINALIZE ===========
        params = {
            'command': 'FINALIZE',
            'media_id': media_id,
        }
        response = self._session.post(
            Endpoint.UPLOAD_MEDIA,
            params=params,
            headers=self.base_headers,
        ).json()

        return response['media_id_string']

    def create_poll(
        self,
        choices: list[str],
        duration_minutes: int
    ) -> str:
        """
        Creates a poll and returns card-uri.

        Parameters
        ----------
        choices : list[str]
            A list of choices for the poll. Maximum of 4 choices.
        duration_minutes : int
            The duration of the poll in minutes.

        Returns
        -------
        str
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
            'twitter:long:duration_minutes': duration_minutes
        }

        for i, choice in enumerate(choices, 1):
            card_data[f'twitter:string:choice{i}_label'] = choice

        data = parse.urlencode(
            {'card_data': card_data}
        ).replace('%27', '%22')
        headers = self.base_headers | {
            'content-type': 'application/x-www-form-urlencoded'
        }
        response = self._session.post(
            Endpoint.CREATE_CARD,
            data=data,
            headers=headers,
        ).json()

        return response['card_uri']

    def create_tweet(
        self,
        text: str = '',
        media_ids: list[str | int] = None,
        poll_uri: str = None
    ):
        """
        Creates a new tweet on Twitter with the specified
        text, media, and poll.

        Parameters
        ----------
        text : str, default=''
            The text content of the tweet.
        media_ids : list[str | int], optional
            A list of media IDs or URIs to attach to the tweet.
            media IDs can be obtained by using the `upload_media` method.
        poll_uri : str, optional
            The URI of a Twitter poll card to attach to the tweet.
            Poll URIs can be obtained by using the `create_poll` method.

        Returns
        -------
        dict
            The JSON response containing information about the created tweet.

        Examples
        --------
        **Create a tweet with media**

        >>> tweet_text = 'Example text'
        >>> media_ids = [
        ...     client.upload_media('image1.png', 0),
        ...     client.upload_media('image1.png', 1)
        ... ]
        >>> client.create_tweet(
        ...     tweet_text,
        ...     media_ids=media_ids
        ... )

        **Create a tweet with a poll**

        >>> tweet_text = 'Example text'
        >>> poll_choices = ['Option A', 'Option B', 'Option C']
        >>> duration_minutes = 60
        >>> poll_uri = client.create_poll(poll_choices, duration_minutes)
        >>> client.create_tweet(
        ...     tweet_text,
        ...     poll_uri=poll_uri
        ... )

        See Also
        --------
        `Client.upload_media`
        `Client.create_poll`
        """
        media_entities = [
            {'media_id': media_id, 'tagged_users': []}
            for media_id in (media_ids or [])
        ]
        variables = {
            'tweet_text': text,
            'dark_request': False,
            'media': {
                'media_entities': media_entities,
                'possibly_sensitive': False
            },
            'semantic_annotation_ids': [],
        }

        if poll_uri is not None:
            variables['card_uri'] = poll_uri

        data = {
            'variables': variables,
            'queryId': 'SiM_cAu83R0wnrpmKQQSEw',
            'features': FEATURES,
        }
        response = self._session.post(
            Endpoint.CREATE_TWEET,
            data=json.dumps(data),
            headers=self.base_headers,
        )
        return response

    def get_user_by_screen_name(self, screen_name: str) -> User:
        """
        Fetches a Twitter user by screen name.

        Parameter
        ---------
        screen_name : str
            The screen name of the Twitter user.

        Returns
        -------
        User
            An instance of the User class representing the Twitter user.

        Examples
        --------
        >>> target_screen_name = 'example_user'
        >>> user_object = client.get_user_by_name(target_screen_name)
        >>> print(user_object)
        <User screen_name="example_user">
        """
        variables = {
            'screen_name': screen_name,
            'withSafetyModeUserFields': False
        }
        params = {
            'variables': json.dumps(variables),
            'features': json.dumps(USER_FEATURES),
            'fieldToggles': json.dumps({'withAuxiliaryUserLabels': False})
        }
        response = self._session.get(
            Endpoint.USER_BY_SCREEN_NAME,
            params=params,
            headers=self.base_headers
        ).json()
        user_data = response['data']['user']['result']
        return User(self, user_data)

    def get_user_tweets(
        self,
        user_id: str,
        count: int = 40,
        get_replies: bool = False,
        cursor: str = None
    ) -> Result[Tweet]:
        """
        Fetches tweets from a specific user's timeline.

        Parameters
        ----------
        user_id : str
            The ID of the Twitter user whose tweets to retrieve.
            To get the user id from the screen name, you can use
            `get_user_by_screen_name` method.
        count : int, default=40
            The number of tweets to retrieve.
        get_replies : bool, default=False
            Whether to include replies to the searched tweets.
        cursor : str, optional
            The cursor for fetching the next set of results.

        Returns
        -------
        Result[Tweet]
            A Result object containing a list of `Tweet` objects.

        Examples
        --------
        >>> user_id = '123456789'

        * If you only have the screen name, you can get the user id as follows:
        >>> screen_name = 'example_user'
        >>> user = client.get_user_by_screen_name(screen_name)
        >>> user_id = user.id

        >>> tweets = client.get_user_tweets(user_id)
        >>> for tweet in tweets:
        ...    print(tweet)
        <Tweet id="tweet_1">
        <Tweet id="tweet_2">
        ...
        ...

        >>> more_tweets = tweets.next  # Retrieve more tweets
        >>> for tweet in more_tweets:
        ...     print(tweet)
        <Tweet id="more_tweet_1">
        <Tweet id="more_tweet_2">
        ...
        ...

        See Also
        --------
        `Client.get_user_by_screen_name`
        """
        variables = {
            'userId': user_id,
            'count': count,
            'includePromotedContent': True,
            'withQuickPromoteEligibilityTweetFields': True,
            'withVoice': True,
            'withV2Timeline': True
        }
        if cursor is not None:
            variables['cursor'] = cursor
        params = {
            'variables': json.dumps(variables),
            'features': json.dumps(FEATURES),
        }
        endpoint = (
            Endpoint.USER_TWEETS_AND_REPLIES
            if get_replies
            else Endpoint.USER_TWEETS
        )
        response = self._session.get(
            endpoint,
            params=params,
            headers=self.base_headers
        ).json()
        instructions = find_dict(response, 'instructions')[0]

        items = instructions[-1]['entries']
        user_info = find_dict(items, 'user_results')[0]['result']
        user = User(self, user_info)
        next_cursor = items[-1]['content']['value']

        tweets = []
        for item in items:
            if 'itemContent' not in item['content']:
                continue
            tweet_info = find_dict(item, 'result')[0]
            tweets.append(Tweet(self, tweet_info, user))

        return Result(
            tweets,
            lambda:self.get_user_tweets(
                user_id, count, get_replies, next_cursor),
            next_cursor
        )
