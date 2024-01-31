from __future__ import annotations

from typing import Any, Callable, Generic, Iterator, TypeVar
from urllib import parse

TOKEN = 'AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'

FEATURES = {
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

USER_FEATURES = {
    'hidden_profile_likes_enabled': True,
    'hidden_profile_subscriptions_enabled': True,
    'responsive_web_graphql_exclude_directive_enabled': True,
    'verified_phone_label_enabled': False,
    'subscriptions_verification_info_is_identity_verified_enabled': True,
    'subscriptions_verification_info_verified_since_enabled': True,
    'highlights_tweets_tab_ui_enabled': True,
    'responsive_web_twitter_article_notes_tab_enabled': False,
    'creator_subscriptions_tweet_preview_api_enabled': True,
    'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
    'responsive_web_graphql_timeline_navigation_enabled': True
}


class Endpoint:
    """
    A class containing Twitter API endpoints.
    """
    TASK = 'https://api.twitter.com/1.1/onboarding/task.json'
    LOGOUT = 'https://api.twitter.com/1.1/account/logout.json'
    CREATE_TWEET = 'https://twitter.com/i/api/graphql/SiM_cAu83R0wnrpmKQQSEw/CreateTweet'
    SEARCH_TIMELINE = 'https://twitter.com/i/api/graphql/HgiQ8U_E6g-HE_I6Pp_2UA/SearchTimeline'
    UPLOAD_MEDIA = 'https://upload.twitter.com/i/media/upload.json'
    GUEST_TOKEN = 'https://api.twitter.com/1.1/guest/activate.json'
    CREATE_CARD = 'https://caps.twitter.com/v2/cards/create.json'
    USER_BY_SCREEN_NAME = 'https://twitter.com/i/api/graphql/NimuplG1OB7Fd2btCLdBOw/UserByScreenName'
    USER_TWEETS = 'https://twitter.com/i/api/graphql/QWF3SzpHmykQHsQMixG0cg/UserTweets'
    USER_TWEETS_AND_REPLIES = 'https://twitter.com/i/api/graphql/vMkJyzx1wdmvOeeNG0n6Wg/UserTweetsAndReplies'
    USER_MEDIA = 'https://twitter.com/i/api/graphql/2tLOJWwGuCTytDrGBg8VwQ/UserMedia'
    USER_LIKES = 'https://twitter.com/i/api/graphql/IohM3gxQHfvWePH5E3KuNA/Likes'
    TWEET_DETAIL = 'https://twitter.com/i/api/graphql/U0HTv-bAWTBYylwEMT7x5A/TweetDetail'
    TREND = 'https://twitter.com/i/api/2/guide.json'
    FAVORITE_TWEET = 'https://twitter.com/i/api/graphql/lI07N6Otwv1PhnEgXILM7A/FavoriteTweet'
    UNFAVORITE_TWEET = 'https://twitter.com/i/api/graphql/ZYKSe-w7KEslx3JhSIk5LA/UnfavoriteTweet'
    CREATE_RETWEET = 'https://twitter.com/i/api/graphql/ojPdsZsimiJrUGLR1sjUtA/CreateRetweet'
    DELETE_RETWEET = 'https://twitter.com/i/api/graphql/iQtK4dl5hBmXewYZuEOKVw/DeleteRetweet'
    CREATE_BOOKMARK = 'https://twitter.com/i/api/graphql/aoDbu3RHznuiSkQ9aNM67Q/CreateBookmark'
    DELETE_BOOKMARK = 'https://twitter.com/i/api/graphql/Wlmlj2-xzyS1GN3a6cj-mQ/DeleteBookmark'
    CREATE_FRIENDSHIPS = 'https://twitter.com/i/api/1.1/friendships/create.json'
    DESTROY_FRIENDSHIPS = 'https://twitter.com/i/api/1.1/friendships/destroy.json'
    HOME_TIMELINE = 'https://twitter.com/i/api/graphql/-X_hcgQzmHGl29-UXxz4sw/HomeTimeline'

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
        fetch_next_result: Callable = None,
        token: str = None
    ) -> None:
        self.__results = results
        self.token = token
        self.__fetch_next_result = fetch_next_result

    @property
    def next(self) -> Result[T]:
        """
        The next result.
        """
        return self.__fetch_next_result()

    def __iter__(self) -> Iterator[T]:
        yield from self.__results

    def __getitem__(self, index: int) -> T:
        return self.__results[index]

    def __repr__(self) -> str:
        return self.__results.__repr__()


def find_dict(obj: list | dict, key: str | int) -> list[Any]:
    """
    Retrieves elements from a nested dictionary.
    """
    results = []
    if isinstance(obj, dict):
        if key in obj:
            results.append(obj.get(key))
    if isinstance(obj, (list, dict)):
        for elem in (obj if isinstance(obj, list) else obj.values()):
            results += find_dict(elem, key)
    return results


def get_query_id(url: str) -> str:
    """
    Extracts the identifier from a URL.

    Examples
    --------
    >>> get_query_id('https://twitter.com/i/api/graphql/queryid/...')
    'queryid'
    """
    return url.rsplit('/', 2)[-2]


def urlencode(data: dict[str, Any]) -> str:
    """
    Encodes a dictionary into a URL-encoded string.
    """
    data_encoded = parse.urlencode(data)
    # replace single quote to double quote.
    return data_encoded.replace('%27', '%22')
