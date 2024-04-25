from __future__ import annotations

import base64
import json
from datetime import datetime
from typing import Any, TYPE_CHECKING, Callable, Generic, Iterator, Literal, TypedDict, TypeVar
from urllib import parse

if TYPE_CHECKING:
    from .client import Client

# This token is common to all accounts and does not need to be changed.
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
    'responsive_web_enhance_cards_enabled': False,
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
    'responsive_web_graphql_timeline_navigation_enabled': True,
}

LIST_FEATURES = {
    'responsive_web_graphql_exclude_directive_enabled': True,
    'verified_phone_label_enabled': False,
    'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
    'responsive_web_graphql_timeline_navigation_enabled': True,
}

COMMUNITY_NOTE_FEATURES = {
    'responsive_web_birdwatch_media_notes_enabled': True,
    'responsive_web_graphql_timeline_navigation_enabled': True,
    'rweb_tipjar_consumption_enabled': False,
    'responsive_web_graphql_exclude_directive_enabled': True,
    'verified_phone_label_enabled': False,
    'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
}

COMMUNITY_TWEETS_FEATURES = {
    'rweb_tipjar_consumption_enabled': True,
    'responsive_web_graphql_exclude_directive_enabled': True,
    'verified_phone_label_enabled': False,
    'creator_subscriptions_tweet_preview_api_enabled': True,
    'responsive_web_graphql_timeline_navigation_enabled': True,
    'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
    'communities_web_enable_tweet_community_results_fetch': True,
    'c9s_tweet_anatomy_moderator_badge_enabled': True,
    'tweetypie_unmention_optimization_enabled': True,
    'responsive_web_edit_tweet_api_enabled': True,
    'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
    'view_counts_everywhere_api_enabled': True,
    'longform_notetweets_consumption_enabled': True,
    'responsive_web_twitter_article_tweet_consumption_enabled': True,
    'tweet_awards_web_tipping_enabled': False,
    'creator_subscriptions_quote_tweet_preview_enabled': False,
    'freedom_of_speech_not_reach_fetch_enabled': True,
    'standardized_nudges_misinfo': True,
    'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
    'rweb_video_timestamps_enabled': True,
    'longform_notetweets_rich_text_read_enabled': True,
    'longform_notetweets_inline_media_enabled': True,
    'responsive_web_enhance_cards_enabled': False,
}

JOIN_COMMUNITY_FEATURES = {
    'rweb_tipjar_consumption_enabled': True,
    'responsive_web_graphql_exclude_directive_enabled': True,
    'verified_phone_label_enabled': False,
    'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
    'responsive_web_graphql_timeline_navigation_enabled': True,
}

NOTE_TWEET_FEATURES = {
    'communities_web_enable_tweet_community_results_fetch': True,
    'c9s_tweet_anatomy_moderator_badge_enabled': True,
    'tweetypie_unmention_optimization_enabled': True,
    'responsive_web_edit_tweet_api_enabled': True,
    'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
    'view_counts_everywhere_api_enabled': True,
    'longform_notetweets_consumption_enabled': True,
    'responsive_web_twitter_article_tweet_consumption_enabled': True,
    'tweet_awards_web_tipping_enabled': False,
    'creator_subscriptions_quote_tweet_preview_enabled': False,
    'longform_notetweets_rich_text_read_enabled': True,
    'longform_notetweets_inline_media_enabled': True,
    'articles_preview_enabled': False,
    'rweb_video_timestamps_enabled': True,
    'rweb_tipjar_consumption_enabled': True,
    'responsive_web_graphql_exclude_directive_enabled': True,
    'verified_phone_label_enabled': False,
    'freedom_of_speech_not_reach_fetch_enabled': True,
    'standardized_nudges_misinfo': True,
    'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
    'tweet_with_visibility_results_prefer_gql_media_interstitial_enabled': True,
    'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
    'responsive_web_graphql_timeline_navigation_enabled': True,
    'responsive_web_enhance_cards_enabled': False,
}

SIMILAR_POSTS_FEATURES = {
    'rweb_tipjar_consumption_enabled': True,
    'responsive_web_graphql_exclude_directive_enabled': True,
    'verified_phone_label_enabled': False,
    'creator_subscriptions_tweet_preview_api_enabled': True,
    'responsive_web_graphql_timeline_navigation_enabled': True,
    'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
    'communities_web_enable_tweet_community_results_fetch': True,
    'c9s_tweet_anatomy_moderator_badge_enabled': True,
    'articles_preview_enabled': False,
    'tweetypie_unmention_optimization_enabled': True,
    'responsive_web_edit_tweet_api_enabled': True,
    'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
    'view_counts_everywhere_api_enabled': True,
    'longform_notetweets_consumption_enabled': True,
    'responsive_web_twitter_article_tweet_consumption_enabled': True,
    'tweet_awards_web_tipping_enabled': False,
    'creator_subscriptions_quote_tweet_preview_enabled': False,
    'freedom_of_speech_not_reach_fetch_enabled': True,
    'standardized_nudges_misinfo': True,
    'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
    'tweet_with_visibility_results_prefer_gql_media_interstitial_enabled': True,
    'rweb_video_timestamps_enabled': True,
    'longform_notetweets_rich_text_read_enabled': True,
    'longform_notetweets_inline_media_enabled': True,
    'responsive_web_enhance_cards_enabled': False,
}

BOOKMARK_FOLDER_TIMELINE_FEATURES = {
    'rweb_tipjar_consumption_enabled': True,
    'responsive_web_graphql_exclude_directive_enabled': True,
    'verified_phone_label_enabled': False,
    'creator_subscriptions_tweet_preview_api_enabled': True,
    'responsive_web_graphql_timeline_navigation_enabled': True,
    'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
    'communities_web_enable_tweet_community_results_fetch': True,
    'c9s_tweet_anatomy_moderator_badge_enabled': True,
    'articles_preview_enabled': False,
    'tweetypie_unmention_optimization_enabled': True,
    'responsive_web_edit_tweet_api_enabled': True,
    'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
    'view_counts_everywhere_api_enabled': True,
    'longform_notetweets_consumption_enabled': True,
    'responsive_web_twitter_article_tweet_consumption_enabled': True,
    'tweet_awards_web_tipping_enabled': False,
    'creator_subscriptions_quote_tweet_preview_enabled': False,
    'freedom_of_speech_not_reach_fetch_enabled': True,
    'standardized_nudges_misinfo': True,
    'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
    'tweet_with_visibility_results_prefer_gql_media_interstitial_enabled': True,
    'rweb_video_timestamps_enabled': True,
    'longform_notetweets_rich_text_read_enabled': True,
    'longform_notetweets_inline_media_enabled': True,
    'responsive_web_enhance_cards_enabled': False,
}


class Endpoint:
    """
    A class containing Twitter API endpoints.
    """

    LOGIN_FLOW = 'https://api.twitter.com/1.1/onboarding/task.json'
    LOGOUT = 'https://api.twitter.com/1.1/account/logout.json'
    CREATE_TWEET = 'https://twitter.com/i/api/graphql/SiM_cAu83R0wnrpmKQQSEw/CreateTweet'
    CREATE_NOTE_TWEET = 'https://twitter.com/i/api/graphql/iCUB42lIfXf9qPKctjE5rQ/CreateNoteTweet'
    DELETE_TWEET = 'https://twitter.com/i/api/graphql/VaenaVgh5q5ih7kvyVjgtg/DeleteTweet'
    SEARCH_TIMELINE = 'https://twitter.com/i/api/graphql/flaR-PUMshxFWZWPNpq4zA/SearchTimeline'
    UPLOAD_MEDIA = 'https://upload.twitter.com/i/media/upload.json'
    CREATE_MEDIA_METADATA = 'https://api.twitter.com/1.1/media/metadata/create.json'
    GUEST_TOKEN = 'https://api.twitter.com/1.1/guest/activate.json'
    CREATE_CARD = 'https://caps.twitter.com/v2/cards/create.json'
    USER_BY_SCREEN_NAME = (
        'https://twitter.com/i/api/graphql/NimuplG1OB7Fd2btCLdBOw/UserByScreenName'
    )
    USER_BY_REST_ID = 'https://twitter.com/i/api/graphql/tD8zKvQzwY3kdx5yz6YmOw/UserByRestId'
    USER_TWEETS = 'https://twitter.com/i/api/graphql/QWF3SzpHmykQHsQMixG0cg/UserTweets'
    USER_TWEETS_AND_REPLIES = (
        'https://twitter.com/i/api/graphql/vMkJyzx1wdmvOeeNG0n6Wg/UserTweetsAndReplies'
    )
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
    HOME_LATEST_TIMELINE = (
        'https://twitter.com/i/api/graphql/U0cdisy7QFIoTfu3-Okw0A/HomeLatestTimeline'
    )
    FOLLOWERS = 'https://twitter.com/i/api/graphql/gC_lyAxZOptAMLCJX5UhWw/Followers'
    BLUE_VERIFIED_FOLLOWERS = (
        'https://twitter.com/i/api/graphql/VmIlPJNEDVQ29HfzIhV4mw/BlueVerifiedFollowers'
    )
    FOLLOWING = 'https://twitter.com/i/api/graphql/2vUj-_Ek-UmBVDNtd8OnQA/Following'
    FOLLOWERS_YOU_KNOW = 'https://twitter.com/i/api/graphql/f2tbuGNjfOE8mNUO5itMew/FollowersYouKnow'
    SUBSCRIPTIONS = (
        'https://twitter.com/i/api/graphql/Wsm5ZTCYtg2eH7mXAXPIgw/UserCreatorSubscriptions'
    )
    SEND_DM = 'https://twitter.com/i/api/1.1/dm/new2.json'
    DELETE_DM = 'https://twitter.com/i/api/graphql/BJ6DtxA2llfjnRoRjaiIiw/DMMessageDeleteMutation'
    INBOX_INITIAL_STATE = 'https://twitter.com/i/api/1.1/dm/inbox_initial_state.json'
    CONVERSASION = 'https://twitter.com/i/api/1.1/dm/conversation/{}.json'
    CREATE_SCHEDULED_TWEET = (
        'https://twitter.com/i/api/graphql/LCVzRQGxOaGnOnYH01NQXg/CreateScheduledTweet'
    )
    BOOKMARKS = 'https://twitter.com/i/api/graphql/qToeLeMs43Q8cr7tRYXmaQ/Bookmarks'
    BOOKMARKS_ALL_DELETE = (
        'https://twitter.com/i/api/graphql/skiACZKC1GDYli-M8RzEPQ/BookmarksAllDelete'
    )
    RETWEETERS = 'https://twitter.com/i/api/graphql/X-XEqG5qHQSAwmvy00xfyQ/Retweeters'
    FAVORITERS = 'https://twitter.com/i/api/graphql/LLkw5EcVutJL6y-2gkz22A/Favoriters'
    ADD_MEMBER_TO_GROUP = (
        'https://twitter.com/i/api/graphql/oBwyQ0_xVbAQ8FAyG0pCRA/AddParticipantsMutation'
    )
    CHANGE_GROUP_NAME = 'https://twitter.com/i/api/1.1/dm/conversation/{}/update_name.json'
    CREATE_LIST = 'https://twitter.com/i/api/graphql/EYg7JZU3A1eJ-wr2eygPHQ/CreateList'
    LIST_ADD_MEMBER = 'https://twitter.com/i/api/graphql/lLNsL7mW6gSEQG6rXP7TNw/ListAddMember'
    LIST_LATEST_TWEETS = (
        'https://twitter.com/i/api/graphql/HjsWc-nwwHKYwHenbHm-tw/ListLatestTweetsTimeline'
    )
    UPDATE_LIST = 'https://twitter.com/i/api/graphql/dIEI1sbSAuZlxhE0ggrezA/UpdateList'
    LIST_MEMBERS = 'https://twitter.com/i/api/graphql/BQp2IEYkgxuSxqbTAr1e1g/ListMembers'
    LIST_SUBSCRIBERS = 'https://twitter.com/i/api/graphql/74wGEkaBxrdoXakWTWMxRQ/ListSubscribers'
    MUTE_LIST = 'https://twitter.com/i/api/graphql/ZYyanJsskNUcltu9bliMLA/MuteList'
    UNMUTE_LIST = 'https://twitter.com/i/api/graphql/pMZrHRNsmEkXgbn3tOyr7Q/UnmuteList'
    EDIT_LIST_BANNER = 'https://twitter.com/i/api/graphql/t_DsROHldculsB0B9BUAWw/EditListBanner'
    DELETE_LIST_BANNER = 'https://twitter.com/i/api/graphql/Y90WuxdWugtMRJhkXTdvzg/DeleteListBanner'
    LIST_REMOVE_MEMBER = 'https://twitter.com/i/api/graphql/cvDFkG5WjcXV0Qw5nfe1qQ/ListRemoveMember'
    LIST_BY_REST_ID = 'https://twitter.com/i/api/graphql/9hbYpeVBMq8-yB8slayGWQ/ListByRestId'
    BLOCK_USER = 'https://twitter.com/i/api/1.1/blocks/create.json'
    UNBLOCK_USER = 'https://twitter.com/i/api/1.1/blocks/destroy.json'
    MUTE_USER = 'https://twitter.com/i/api/1.1/mutes/users/create.json'
    UNMUTE_USER = 'https://twitter.com/i/api/1.1/mutes/users/destroy.json'
    MESSAGE_ADD_REACTION = (
        'https://twitter.com/i/api/graphql/VyDyV9pC2oZEj6g52hgnhA/useDMReactionMutationAddMutation'
    )
    MESSAGE_REMOVE_REACTION = 'https://twitter.com/i/api/graphql/bV_Nim3RYHsaJwMkTXJ6ew/useDMReactionMutationRemoveMutation'
    FETCH_SCHEDULED_TWEETS = (
        'https://twitter.com/i/api/graphql/ITtjAzvlZni2wWXwf295Qg/FetchScheduledTweets'
    )
    DELETE_SCHEDULED_TWEET = (
        'https://twitter.com/i/api/graphql/CTOVqej0JBXAZSwkp1US0g/DeleteScheduledTweet'
    )
    SETTINGS = 'https://api.twitter.com/1.1/account/settings.json'
    LIST_MANAGEMENT = (
        'https://twitter.com/i/api/graphql/47170qwZCt5aFo9cBwFoNA/ListsManagementPageTimeline'
    )
    NOTIFICATIONS_ALL = 'https://twitter.com/i/api/2/notifications/all.json'
    NOTIFICATIONS_VERIFIED = 'https://twitter.com/i/api/2/notifications/verified.json'
    NOTIFICATIONS_MENTIONES = 'https://twitter.com/i/api/2/notifications/mentions.json'
    VOTE = 'https://caps.twitter.com/v2/capi/passthrough/1'
    REPORT_FLOW = 'https://twitter.com/i/api/1.1/report/flow.json'
    FETCH_COMMUNITY_NOTE = (
        'https://twitter.com/i/api/graphql/fKWPPj271aTM-AB9Xp48IA/BirdwatchFetchOneNote'
    )
    SEARCH_COMMUNITY = (
        'https://twitter.com/i/api/graphql/daVUkhfHn7-Z8llpYVKJSw/CommunitiesSearchQuery'
    )
    GET_COMMUNITY = 'https://twitter.com/i/api/graphql/lUBKrilodgg9Nikaw3cIiA/CommunityQuery'
    COMMUNITY_TWEETS = (
        'https://twitter.com/i/api/graphql/mhwSsmub4JZgHcs0dtsjrw/CommunityTweetsTimeline'
    )
    COMMUNITY_MEDIA = (
        'https://twitter.com/i/api/graphql/Ht5K2ckaZYAOuRFmFfbHig/CommunityMediaTimeline'
    )
    COMMUNITIES_TIMELINE = (
        'https://twitter.com/i/api/graphql/4-4iuIdaLPpmxKnA3mr2LA/CommunitiesMainPageTimeline'
    )
    JOIN_COMMUNITY = 'https://twitter.com/i/api/graphql/xZQLbDwbI585YTG0QIpokw/JoinCommunity'
    REQUEST_TO_JOIN_COMMUNITY = (
        'https://twitter.com/i/api/graphql/XwWChphD_6g7JnsFus2f2Q/RequestToJoinCommunity'
    )
    LEAVE_COMMUNITY = 'https://twitter.com/i/api/graphql/OoS6Kd4-noNLXPZYHtygeA/LeaveCommunity'
    COMMUNITY_MEMBERS = (
        'https://twitter.com/i/api/graphql/KDAssJ5lafCy-asH4wm1dw/membersSliceTimeline_Query'
    )
    COMMUNITY_MODERATORS = (
        'https://twitter.com/i/api/graphql/9KI_r8e-tgp3--N5SZYVjg/moderatorsSliceTimeline_Query'
    )
    SEARCH_COMMUNITY_TWEET = (
        'https://twitter.com/i/api/graphql/5341rmzzvdjqfmPKfoHUBw/CommunityTweetSearchModuleQuery'
    )
    SIMILAR_POSTS = 'https://twitter.com/i/api/graphql/EToazR74i0rJyZYalfVEAQ/SimilarPosts'
    BOOKMARK_FOLDERS = (
        'https://twitter.com/i/api/graphql/i78YDd0Tza-dV4SYs58kRg/BookmarkFoldersSlice'
    )
    EDIT_BOOKMARK_FOLDER = (
        'https://twitter.com/i/api/graphql/a6kPp1cS1Dgbsjhapz1PNw/EditBookmarkFolder'
    )
    DELETE_BOOKMARK_FOLDER = (
        'https://twitter.com/i/api/graphql/2UTTsO-6zs93XqlEUZPsSg/DeleteBookmarkFolder'
    )
    CREATE_BOOKMARK_FOLDER = (
        'https://twitter.com/i/api/graphql/6Xxqpq8TM_CREYiuof_h5w/createBookmarkFolder'
    )
    BOOKMARK_FOLDER_TIMELINE = (
        'https://twitter.com/i/api/graphql/8HoabOvl7jl9IC1Aixj-vg/BookmarkFolderTimeline'
    )
    BOOKMARK_TO_FOLDER = (
        'https://twitter.com/i/api/graphql/4KHZvvNbHNf07bsgnL9gWA/bookmarkTweetToFolder'
    )


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
        fetch_next_result: Callable | None = None,
        next_cursor: str | None = None,
        fetch_previous_result: Callable | None = None,
        previous_cursor: str | None = None,
    ) -> None:
        self.__results = results
        self.next_cursor = next_cursor
        self.__fetch_next_result = fetch_next_result
        self.previous_cursor = previous_cursor
        self.__fetch_previous_result = fetch_previous_result

    def next(self) -> Result[T]:
        """
        The next result.
        """
        if self.__fetch_next_result is None:
            return Result([])
        return self.__fetch_next_result()

    def previous(self) -> Result[T]:
        """
        The previous result.
        """
        if self.__fetch_previous_result is None:
            return Result([])
        return self.__fetch_previous_result()

    @property
    def cursor(self) -> str:
        """Alias of `next_token`"""
        return self.next_cursor

    @property
    def token(self) -> str:
        """Alias of `next_token`"""
        return self.next_cursor

    def __iter__(self) -> Iterator[T]:
        yield from self.__results

    def __getitem__(self, index: int) -> T:
        return self.__results[index]

    def __len__(self) -> int:
        return len(self.__results)

    def __repr__(self) -> str:
        return self.__results.__repr__()


class Flow:
    def __init__(self, client: Client, endpoint: str, headers: dict) -> None:
        self._client = client
        self.endpoint = endpoint
        self.headers = headers
        self.response = None

    def execute_task(self, *subtask_inputs, **kwargs) -> None:
        data = {}

        if self.token is not None:
            data['flow_token'] = self.token
        if subtask_inputs is not None:
            data['subtask_inputs'] = list(subtask_inputs)

        response = self._client.http.post(
            self.endpoint, data=json.dumps(data), headers=self.headers, **kwargs
        ).json()
        self.response = response

    @property
    def token(self) -> str | None:
        if self.response is None:
            return None
        return self.response.get('flow_token')

    @property
    def task_id(self) -> str | None:
        if self.response is None:
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
        for elem in obj if isinstance(obj, list) else obj.values():
            r = find_dict(elem, key, find_one)
            results += r
            if r and find_one:
                return results
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
            'full_text': raw_data.get('full_text'),
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
            'retweet_count': raw_data.get('retweet_count'),
        },
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
            'profile_banner_url': raw_data.get('profile_banner_url'),
        },
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


FILTERS = Literal[
    'media', 'retweets', 'native_video', 'periscope', 'vine', 'images', 'twimg', 'links'
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
        text += ' ' + ' '.join([f'"{i}"' for i in exact_phrases])

    if or_keywords := options.get('or_keywords'):
        text += ' ' + ' OR '.join(or_keywords)

    if exclude_keywords := options.get('exclude_keywords'):
        text += ' ' + ' '.join([f'-"{i}"' for i in exclude_keywords])

    if hashtags := options.get('hashtags'):
        text += ' ' + ' '.join([f'#{i}' for i in hashtags])

    if from_user := options.get('from_user'):
        text += f' from:{from_user}'

    if to_user := options.get('to_user'):
        text += f' to:{to_user}'

    if mentioned_users := options.get('mentioned_users'):
        text += ' ' + ' '.join([f'@{i}' for i in mentioned_users])

    if filters := options.get('filters'):
        text += ' ' + ' '.join([f'filter:{i}' for i in filters])

    if exclude_filters := options.get('exclude_filters'):
        text += ' ' + ' '.join([f'-filter:{i}' for i in exclude_filters])

    if urls := options.get('urls'):
        text += ' ' + ' '.join([f'url:{i}' for i in urls])

    if since := options.get('since'):
        text += f' since:{since}'

    if until := options.get('until'):
        text += f' until:{until}'

    if options.get('positive') == True:
        text += f' :)'

    if options.get('negative') == True:
        text += f' :('

    if options.get('question') == True:
        text += f' ?'

    return text
