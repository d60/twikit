import json
import pickle
from typing import Literal
import cv2
import os

import requests

from tweet import Tweet
from user import User
from utils import Endpoint, Result, TOKEN


class Client:
    """
    Examples
    --------
    >>> client = Client(token='TOKEN', language='en-US')

    >>> # Specify two out of three: username, email, phone_number
    >>> client.login(
    ...     guest_token='00000000000',
    ...     username='example_user',
    ...     email='email@example.com'
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
            Endpoint.GET_GUEST_TOKEN,
            headers=self.base_headers,
            data={}
        ).json()
        guest_token = response['guest_token']
        return guest_token

    def save_cookies(self, filename: str) -> None:
        """
        Saves cookies to file
        """
        with open(filename, 'wb') as f:
            pickle.dump(self._session.cookies, f)

    def load_cookies(self, filename: str) -> None:
        """
        Loads cookies from a file
        """
        with open(filename, 'rb') as f:
            self._session.cookies.update(pickle.load(f))

    @property
    def base_features(self) -> dict[str, bool]:
        return {
            'creator_subscriptions_tweet_preview_api_enabled': True,
            'c9s_tweet_anatomy_moderator_badge_enabled': True,
            'tweetypie_unmention_optimization_enabled': True,
            'responsive_web_edit_tweet_api_enabled': True,
            'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
            'view_counts_everywhere_api_enabled': True,
            'longform_notetweets_consumption_enabled': True,
            'responsive_web_twitter_article_tweet_consumption_enabled': True,
            'tweet_awards_web_tipping_enabled': False,
            'longform_notetweets_rich_text_read_enabled': True,
            'longform_notetweets_inline_media_enabled': True,
            'rweb_video_timestamps_enabled': True,
            'responsive_web_graphql_exclude_directive_enabled': True,
            'verified_phone_label_enabled': False,
            'freedom_of_speech_not_reach_fetch_enabled': True,
            'standardized_nudges_misinfo': True,
            'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
            'responsive_web_media_download_video_enabled': False,
            'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
            'responsive_web_graphql_timeline_navigation_enabled': True,
            'responsive_web_enhance_cards_enabled': False
        }

    @property
    def base_headers(self) -> dict[str, str]:
        return {
            'authorization': f'Bearer {self._token}',
            'content-type': 'application/json',
            'Accept-Language': self.language
        }

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
        login_info = [i for i in (username, email, phone_number) if i is not None]
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
                            'response_data': {'text_data': {'result': login_info[0]}},
                        }
                    ],
                    'link': 'next_link',
                },
            },
        )
        flow_token = response['flow_token']
        task_id = response['subtasks'][0]['subtask_id']

        if task_id == 'LoginEnterAlternateIdentifierSubtask':
            response = _execute_task(
                flow_token,
                {
                    'subtask_id': 'LoginEnterAlternateIdentifierSubtask',
                    'enter_text': {'text': login_info[1], 'link': 'next_link'},
                }
            )
            flow_token = response['flow_token']

        response = _execute_task(
            flow_token,
            {
                'subtask_id': 'LoginEnterPassword',
                'enter_password': {'password': password, 'link': 'next_link'},
            },
        )
        flow_token = response['flow_token']

        _execute_task(
            flow_token,
            {
                'subtask_id': 'AccountDuplicationCheck',
                'check_logged_in_account': {'link': 'AccountDuplicationCheck_false'},
            },
        )

    def _get_csrf_token(self) -> str:
        """
        Retrieves the Cross-Site Request Forgery (CSRF) token from the
        current session's cookies.

        Returns
        -------
        str
            The CSRF token as a string.
        """
        return self._session.cookies.get_dict()['ct0']

    def _search(self, query: str, product: str, count: int, cursor: str):
        variables = {
            'rawQuery': query,
            'count': count,
            'querySource': 'typed_query',
            'product': product
        }
        if cursor is not None:
            variables['cursor'] = cursor
        features = self.base_features
        params = {
            'variables': json.dumps(variables),
            'features': json.dumps(features)
        }
        headers = self.base_headers | {
            'X-Csrf-Token': self._get_csrf_token()
        }

        response = self._session.get(
            Endpoint.SEARCH_TIMELINE,
            params=(params),
            headers=headers
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
        instructions = response['data']['search_by_raw_query']\
                         ['search_timeline']['timeline']['instructions']

        if cursor is None:
            if product == 'Media':
                items = instructions[-1]['entries'][0]['content']['items']
            else:
                items = instructions[0]['entries']
            next_cursor = instructions[-1]['entries'][-1]['content']['value']
        else:
            if product == 'Media':
                items = instructions[0]['moduleItems']
            else:
                items = instructions[0]['entries']
            next_cursor = instructions[-1]['entry']['content']['value']

        tweets = []
        for item in items:
            if product == 'Media':
                tweet_info = item['item']['itemContent']['tweet_results']['result']
            else:
                if 'itemContent' not in item['content']:
                    continue
                tweet_info = item['content']['itemContent']['tweet_results']['result']
            user_info = tweet_info['core']['user_results']['result']
            tweets.append(Tweet(self, tweet_info, User(self, user_info)))

        return Result(
            tweets,
            lambda:self.search_tweet(query, product, count, next_cursor),
            next_cursor
        )

    def upload_media(self, image):
        headers = self.base_headers | {
            'X-Csrf-Token': self._get_csrf_token(),
            'content-type': 'multipart/form-data',
            'Referer': 'https://twitter.com/',
        }
        params = {
            'command': 'INIT',
            'total_bytes': 3820,
            'media_type': 'image/png',
            'media_category': 'tweet_image'
        }
        return self._session.post(Endpoint.UPLOAD_MEDIA, params=params, headers=headers, data=json.dumps({}))
        # エラー

    def create_tweet(self):
        ...



client = Client('en-US')
client.login(username='', email='', password='')
print(client.upload_media(''))
