from __future__ import annotations

from typing import TYPE_CHECKING

from ..utils import (
    BOOKMARK_FOLDER_TIMELINE_FEATURES,
    COMMUNITY_NOTE_FEATURES,
    COMMUNITY_TWEETS_FEATURES,
    FEATURES,
    JOIN_COMMUNITY_FEATURES,
    LIST_FEATURES,
    NOTE_TWEET_FEATURES,
    SIMILAR_POSTS_FEATURES,
    USER_FEATURES,
    flatten_params,
    get_query_id
)

if TYPE_CHECKING:
    from .client import Client


class Endpoint:
    SEARCH_TIMELINE = 'https://twitter.com/i/api/graphql/flaR-PUMshxFWZWPNpq4zA/SearchTimeline'
    SIMILAR_POSTS = 'https://twitter.com/i/api/graphql/EToazR74i0rJyZYalfVEAQ/SimilarPosts'
    CREATE_NOTE_TWEET = 'https://twitter.com/i/api/graphql/iCUB42lIfXf9qPKctjE5rQ/CreateNoteTweet'
    CREATE_TWEET = 'https://twitter.com/i/api/graphql/SiM_cAu83R0wnrpmKQQSEw/CreateTweet'
    CREATE_SCHEDULED_TWEET = 'https://twitter.com/i/api/graphql/LCVzRQGxOaGnOnYH01NQXg/CreateScheduledTweet'
    DELETE_TWEET = 'https://twitter.com/i/api/graphql/VaenaVgh5q5ih7kvyVjgtg/DeleteTweet'
    USER_BY_SCREEN_NAME = 'https://twitter.com/i/api/graphql/NimuplG1OB7Fd2btCLdBOw/UserByScreenName'
    USER_BY_REST_ID = 'https://twitter.com/i/api/graphql/tD8zKvQzwY3kdx5yz6YmOw/UserByRestId'
    TWEET_DETAIL = 'https://twitter.com/i/api/graphql/U0HTv-bAWTBYylwEMT7x5A/TweetDetail'
    FETCH_SCHEDULED_TWEETS = 'https://twitter.com/i/api/graphql/ITtjAzvlZni2wWXwf295Qg/FetchScheduledTweets'
    DELETE_SCHEDULED_TWEET = 'https://twitter.com/i/api/graphql/CTOVqej0JBXAZSwkp1US0g/DeleteScheduledTweet'
    RETWEETERS = 'https://twitter.com/i/api/graphql/X-XEqG5qHQSAwmvy00xfyQ/Retweeters'
    FAVORITERS = 'https://twitter.com/i/api/graphql/LLkw5EcVutJL6y-2gkz22A/Favoriters'
    FETCH_COMMUNITY_NOTE = 'https://twitter.com/i/api/graphql/fKWPPj271aTM-AB9Xp48IA/BirdwatchFetchOneNote'
    USER_TWEETS = 'https://twitter.com/i/api/graphql/QWF3SzpHmykQHsQMixG0cg/UserTweets'
    USER_TWEETS_AND_REPLIES = 'https://twitter.com/i/api/graphql/vMkJyzx1wdmvOeeNG0n6Wg/UserTweetsAndReplies'
    USER_MEDIA = 'https://twitter.com/i/api/graphql/2tLOJWwGuCTytDrGBg8VwQ/UserMedia'
    USER_LIKES = 'https://twitter.com/i/api/graphql/IohM3gxQHfvWePH5E3KuNA/Likes'
    HOME_TIMELINE = 'https://twitter.com/i/api/graphql/-X_hcgQzmHGl29-UXxz4sw/HomeTimeline'
    HOME_LATEST_TIMELINE = 'https://twitter.com/i/api/graphql/U0cdisy7QFIoTfu3-Okw0A/HomeLatestTimeline'
    FAVORITE_TWEET = 'https://twitter.com/i/api/graphql/lI07N6Otwv1PhnEgXILM7A/FavoriteTweet'
    UNFAVORITE_TWEET = 'https://twitter.com/i/api/graphql/ZYKSe-w7KEslx3JhSIk5LA/UnfavoriteTweet'
    CREATE_RETWEET = 'https://twitter.com/i/api/graphql/ojPdsZsimiJrUGLR1sjUtA/CreateRetweet'
    DELETE_RETWEET = 'https://twitter.com/i/api/graphql/iQtK4dl5hBmXewYZuEOKVw/DeleteRetweet'
    CREATE_BOOKMARK = 'https://twitter.com/i/api/graphql/aoDbu3RHznuiSkQ9aNM67Q/CreateBookmark'
    BOOKMARK_TO_FOLDER = 'https://twitter.com/i/api/graphql/4KHZvvNbHNf07bsgnL9gWA/bookmarkTweetToFolder'
    DELETE_BOOKMARK = 'https://twitter.com/i/api/graphql/Wlmlj2-xzyS1GN3a6cj-mQ/DeleteBookmark'
    BOOKMARKS = 'https://twitter.com/i/api/graphql/qToeLeMs43Q8cr7tRYXmaQ/Bookmarks'
    BOOKMARK_FOLDER_TIMELINE = 'https://twitter.com/i/api/graphql/8HoabOvl7jl9IC1Aixj-vg/BookmarkFolderTimeline'
    BOOKMARKS_ALL_DELETE = 'https://twitter.com/i/api/graphql/skiACZKC1GDYli-M8RzEPQ/BookmarksAllDelete'
    BOOKMARK_FOLDERS_SLICE = 'https://twitter.com/i/api/graphql/i78YDd0Tza-dV4SYs58kRg/BookmarkFoldersSlice'
    EDIT_BOOKMARK_FOLDER = 'https://twitter.com/i/api/graphql/a6kPp1cS1Dgbsjhapz1PNw/EditBookmarkFolder'
    DELETE_BOOKMARK_FOLDER = 'https://twitter.com/i/api/graphql/2UTTsO-6zs93XqlEUZPsSg/DeleteBookmarkFolder'
    CREATE_BOOKMARK_FOLDER = 'https://twitter.com/i/api/graphql/6Xxqpq8TM_CREYiuof_h5w/createBookmarkFolder'
    FOLLOWERS = 'https://twitter.com/i/api/graphql/gC_lyAxZOptAMLCJX5UhWw/Followers'
    BLUE_VERIFIED_FOLLOWERS = 'https://twitter.com/i/api/graphql/VmIlPJNEDVQ29HfzIhV4mw/BlueVerifiedFollowers'
    FOLLOWERS_YOU_KNOW = 'https://twitter.com/i/api/graphql/f2tbuGNjfOE8mNUO5itMew/FollowersYouKnow'
    FOLLOWING = 'https://twitter.com/i/api/graphql/2vUj-_Ek-UmBVDNtd8OnQA/Following'
    USER_CREATOR_SUBSCRIPTIONS = 'https://twitter.com/i/api/graphql/Wsm5ZTCYtg2eH7mXAXPIgw/UserCreatorSubscriptions'
    USER_DM_REACTION_MUTATION_ADD_MUTATION = 'https://twitter.com/i/api/graphql/VyDyV9pC2oZEj6g52hgnhA/useDMReactionMutationAddMutation'
    USER_DM_REACTION_MUTATION_REMOVE_MUTATION = 'https://twitter.com/i/api/graphql/bV_Nim3RYHsaJwMkTXJ6ew/useDMReactionMutationRemoveMutation'
    DM_MESSAGE_DELETE_MUTATION = 'https://twitter.com/i/api/graphql/BJ6DtxA2llfjnRoRjaiIiw/DMMessageDeleteMutation'
    ADD_PARTICIPANTS_MUTATION = 'https://twitter.com/i/api/graphql/oBwyQ0_xVbAQ8FAyG0pCRA/AddParticipantsMutation'
    CREATE_LIST = 'https://twitter.com/i/api/graphql/EYg7JZU3A1eJ-wr2eygPHQ/CreateList'
    EDIT_LIST_BANNER = 'https://twitter.com/i/api/graphql/t_DsROHldculsB0B9BUAWw/EditListBanner'
    DELETE_LIST_BANNER = 'https://twitter.com/i/api/graphql/Y90WuxdWugtMRJhkXTdvzg/DeleteListBanner'
    UPDATE_LIST = 'https://twitter.com/i/api/graphql/dIEI1sbSAuZlxhE0ggrezA/UpdateList'
    LIST_ADD_MEMBER = 'https://twitter.com/i/api/graphql/lLNsL7mW6gSEQG6rXP7TNw/ListAddMember'
    LIST_REMOVE_MEMBER = 'https://twitter.com/i/api/graphql/cvDFkG5WjcXV0Qw5nfe1qQ/ListRemoveMember'
    LIST_MANAGEMENT_PACE_TIMELINE = 'https://twitter.com/i/api/graphql/47170qwZCt5aFo9cBwFoNA/ListsManagementPageTimeline'
    LIST_BY_REST_ID = 'https://twitter.com/i/api/graphql/9hbYpeVBMq8-yB8slayGWQ/ListByRestId'
    LIST_LATEST_TWEETS_TIMELINE = 'https://twitter.com/i/api/graphql/HjsWc-nwwHKYwHenbHm-tw/ListLatestTweetsTimeline'
    LIST_MEMBERS = 'https://twitter.com/i/api/graphql/BQp2IEYkgxuSxqbTAr1e1g/ListMembers'
    LIST_SUBSCRIBERS = 'https://twitter.com/i/api/graphql/74wGEkaBxrdoXakWTWMxRQ/ListSubscribers'
    SEARCH_COMMUNITY = 'https://twitter.com/i/api/graphql/daVUkhfHn7-Z8llpYVKJSw/CommunitiesSearchQuery'
    COMMUNITY_QUERY = 'https://twitter.com/i/api/graphql/lUBKrilodgg9Nikaw3cIiA/CommunityQuery'
    COMMUNITY_MEDIA_TIMELINE = 'https://twitter.com/i/api/graphql/Ht5K2ckaZYAOuRFmFfbHig/CommunityMediaTimeline'
    COMMUNITY_TWEETS_TIMELINE = 'https://twitter.com/i/api/graphql/mhwSsmub4JZgHcs0dtsjrw/CommunityTweetsTimeline'
    COMMUNITIES_MAIN_PAGE_TIMELINE = 'https://twitter.com/i/api/graphql/4-4iuIdaLPpmxKnA3mr2LA/CommunitiesMainPageTimeline'
    JOIN_COMMUNITY = 'https://twitter.com/i/api/graphql/xZQLbDwbI585YTG0QIpokw/JoinCommunity'
    LEAVE_COMMUNITY = 'https://twitter.com/i/api/graphql/OoS6Kd4-noNLXPZYHtygeA/LeaveCommunity'
    REQUEST_TO_JOIN_COMMUNITY = 'https://twitter.com/i/api/graphql/XwWChphD_6g7JnsFus2f2Q/RequestToJoinCommunity'
    MEMBERS_SLICE_TIMELINE_QUERY = 'https://twitter.com/i/api/graphql/KDAssJ5lafCy-asH4wm1dw/membersSliceTimeline_Query'
    MODERATORS_SLICE_TIMELINE_QUERY = 'https://twitter.com/i/api/graphql/9KI_r8e-tgp3--N5SZYVjg/moderatorsSliceTimeline_Query'
    COMMUNITY_TWEET_SEARCH_MODULE_QUERY = 'https://twitter.com/i/api/graphql/5341rmzzvdjqfmPKfoHUBw/CommunityTweetSearchModuleQuery'


class GQLClient:
    def __init__(self, base: Client) -> None:
        self.base = base

    async def gql_get(
        self,
        url: str,
        variables: dict,
        features: dict | None = None,
        headers: dict | None = None,
        extra_params: dict | None = None,
        **kwargs
    ):
        params = {'variables': variables}
        if features is not None:
            params['features'] = features
        if extra_params is not None:
            params |= extra_params
        if headers is None:
            headers = self.base._base_headers

        return await self.base.get(url, params=flatten_params(params), headers=headers, **kwargs)

    async def gql_post(
        self,
        url: str,
        variables: dict,
        features: dict | None = None,
        headers: dict | None = None,
        extra_data: dict | None = None,
        **kwargs
    ):
        data = {'variables': variables, 'queryId': get_query_id(url)}
        if features is not None:
            data['features'] = features
        if extra_data is not None:
            data |= extra_data
        if headers is None:
            headers = self.base._base_headers

        return await self.base.post(url, json=data, headers=headers, **kwargs)

    async def search_timeline(
        self,
        query: str,
        product: str,
        count: int,
        cursor: str | None
    ):
        variables = {
            'rawQuery': query,
            'count': count,
            'querySource': 'typed_query',
            'product': product
        }
        if cursor is not None:
            variables['cursor'] = cursor
        return await self.gql_get(Endpoint.SEARCH_TIMELINE, variables, FEATURES)

    async def similar_posts(self, tweet_id: str):
        variables = {'tweet_id': tweet_id}
        return await self.gql_get(
            Endpoint.SIMILAR_POSTS,
            variables,
            SIMILAR_POSTS_FEATURES
        )

    async def create_tweet(
        self, is_note_tweet, text, media_entities,
        poll_uri, reply_to, attachment_url,
        community_id, share_with_followers,
        richtext_options, edit_tweet_id, limit_mode
    ):
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

        if reply_to is not None:
            variables['reply'] = {
                'in_reply_to_tweet_id': reply_to,
                'exclude_reply_user_ids': []
            }

        if limit_mode is not None:
            variables['conversation_control'] = {'mode': limit_mode}

        if attachment_url is not None:
            variables['attachment_url'] = attachment_url

        if community_id is not None:
            variables['semantic_annotation_ids'] = [{
                'entity_id': community_id,
                'group_id': '8',
                'domain_id': '31'
            }]
            variables['broadcast'] = share_with_followers

        if richtext_options is not None:
            is_note_tweet = True
            variables['richtext_options'] = {
                'richtext_tags': richtext_options
            }
        if edit_tweet_id is not None:
            variables['edit_options'] = {
                'previous_tweet_id': edit_tweet_id
            }

        if is_note_tweet:
            endpoint = Endpoint.CREATE_NOTE_TWEET
            features = NOTE_TWEET_FEATURES
        else:
            endpoint = Endpoint.CREATE_TWEET
            features = FEATURES
        # data = {
        #     'variables': variables,
        #     'queryId': get_query_id(Endpoint.CREATE_TWEET),
        #     'features': features,
        # }
        return await self.gql_post(endpoint, variables, features)
        # return await self.base.post(
        #     endpoint,
        #     json=data,
        #     headers=self.base._base_headers,
        # )

    async def create_scheduled_tweet(self, scheduled_at, text, media_ids) -> str:
        variables = {
            'post_tweet_request': {
            'auto_populate_reply_metadata': False,
            'status': text,
            'exclude_reply_user_ids': [],
            'media_ids': media_ids
            },
            'execute_at': scheduled_at
        }
        data = {
            'variables': variables,
            'queryId': get_query_id(Endpoint.CREATE_SCHEDULED_TWEET),
        }
        return await self.base.post(
            Endpoint.CREATE_SCHEDULED_TWEET,
            json=data,
            headers=self.base._base_headers,
        )

    async def delete_tweet(self, tweet_id):
        data = {
            'variables': {
                'tweet_id': tweet_id,
                'dark_request': False
            },
            'queryId': get_query_id(Endpoint.DELETE_TWEET)
        }
        return await self.base.post(
            Endpoint.DELETE_TWEET,
            json=data,
            headers=self.base._base_headers
        )

    async def user_by_screen_name(self, screen_name):
        variables = {
            'screen_name': screen_name,
            'withSafetyModeUserFields': False
        }
        params = flatten_params({
            'variables': variables,
            'features': USER_FEATURES,
            'fieldToggles': {'withAuxiliaryUserLabels': False}
        })
        return await self.base.get(
            Endpoint.USER_BY_SCREEN_NAME,
            params=params,
            headers=self.base._base_headers
        )

    async def user_by_rest_id(self, user_id):
        variables = {
            'userId': user_id,
            'withSafetyModeUserFields': True
        }
        params = flatten_params({
            'variables': variables,
            'features': USER_FEATURES
        })
        return await self.base.get(
            Endpoint.USER_BY_REST_ID,
            params=params,
            headers=self.base._base_headers
        )

    async def tweet_detail(self, tweet_id, cursor):
        variables = {
            'focalTweetId': tweet_id,
            'with_rux_injections': False,
            'includePromotedContent': True,
            'withCommunity': True,
            'withQuickPromoteEligibilityTweetFields': True,
            'withBirdwatchNotes': True,
            'withVoice': True,
            'withV2Timeline': True
        }
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({
            'variables': variables,
            'features': FEATURES,
            'fieldToggles': {'withAuxiliaryUserLabels': False}
        })
        return await self.base.get(
            Endpoint.TWEET_DETAIL,
            params=params,
            headers=self.base._base_headers
        )

    async def fetch_scheduled_tweets(self):
        params = flatten_params({'variables': {'ascending': True}})
        return await self.base.get(
            Endpoint.FETCH_SCHEDULED_TWEETS,
            params=params,
            headers=self.base._base_headers
        )

    async def delete_scheduled_tweet(self, tweet_id):
        data = {
            'variables': {'scheduled_tweet_id': tweet_id},
            'queryId': get_query_id(Endpoint.DELETE_SCHEDULED_TWEET)
        }
        return await self.base.post(
            Endpoint.DELETE_SCHEDULED_TWEET,
            json=data,
            headers=self.base._base_headers
        )

    async def tweet_engagements(self, tweet_id, count, cursor, endpoint):
        variables = {
            'tweetId': tweet_id,
            'count': count,
            'includePromotedContent': True
        }
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({
            'variables': variables,
            'features': FEATURES
        })
        return await self.base.get(
            endpoint,
            params=params,
            headers=self.base._base_headers
        )

    async def retweeters(self, tweet_id, count, cursor):
        return self.tweet_engagements(tweet_id, count, cursor, Endpoint.RETWEETERS)

    async def favoriters(self, tweet_id, count, cursor):
        return self.tweet_engagements(tweet_id, count, cursor, Endpoint.FAVORITERS)

    async def bird_watch_one_note(self, note_id):
        params = flatten_params({
            'variables': {'note_id': note_id},
            'features': COMMUNITY_NOTE_FEATURES
        })
        return await self.base.get(
            Endpoint.FETCH_COMMUNITY_NOTE,
            params=params,
            headers=self.base._base_headers
        )

    async def _get_user_tweets(self, user_id, count, cursor, endpoint):
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
        params = flatten_params({
            'variables': variables,
            'features': FEATURES
        })
        return await self.base.get(
            endpoint,
            params=params,
            headers=self.base._base_headers
        )

    async def user_tweets(self, user_id, count, cursor):
        return self._get_user_tweets(user_id, count, cursor, Endpoint.USER_TWEETS)

    async def user_tweets_and_replies(self, user_id, count, cursor):
        return self._get_user_tweets(user_id, count, cursor, Endpoint.USER_TWEETS_AND_REPLIES)

    async def user_media(self, user_id, count, cursor):
        return self._get_user_tweets(user_id, count, cursor, Endpoint.USER_MEDIA)

    async def user_likes(self, user_id, count, cursor):
        return self._get_user_tweets(user_id, count, cursor, Endpoint.USER_LIKES)

    async def home_timeline(self, count, seen_tweet_ids, cursor):
        variables = {
            "count": count,
            "includePromotedContent": True,
            "latestControlAvailable": True,
            "requestContext": "launch",
            "withCommunity": True,
            "seenTweetIds": seen_tweet_ids or []
        }
        if cursor is not None:
            variables['cursor'] = cursor
        data = {
            'variables': variables,
            'queryId': get_query_id(Endpoint.HOME_TIMELINE),
            'features': FEATURES,
        }
        return await self.base.post(
            Endpoint.HOME_TIMELINE,
            json=data,
            headers=self.base._base_headers
        )

    async def home_latest_timeline(self, count, seen_tweet_ids, cursor):
        variables = {
            "count": count,
            "includePromotedContent": True,
            "latestControlAvailable": True,
            "requestContext": "launch",
            "withCommunity": True,
            "seenTweetIds": seen_tweet_ids or []
        }
        if cursor is not None:
            variables['cursor'] = cursor
        data = {
            'variables': variables,
            'queryId': get_query_id(Endpoint.HOME_LATEST_TIMELINE),
            'features': FEATURES,
        }
        return await self.base.post(
            Endpoint.HOME_LATEST_TIMELINE,
            json=data,
            headers=self.base._base_headers
        )

    async def favorite_tweet(self, tweet_id):
        data = {
            'variables': {'tweet_id': tweet_id},
            'queryId': get_query_id(Endpoint.FAVORITE_TWEET)
        }
        return await self.base.post(
            Endpoint.FAVORITE_TWEET,
            json=data,
            headers=self.base._base_headers
        )

    async def unfavorite_tweet(self, tweet_id):
        data = {
            'variables': {'tweet_id': tweet_id},
            'queryId': get_query_id(Endpoint.UNFAVORITE_TWEET)
        }
        return await self.base.post(
            Endpoint.UNFAVORITE_TWEET,
            json=data,
            headers=self.base._base_headers
        )

    async def retweet(self, tweet_id):
        data = {
            'variables': {'tweet_id': tweet_id, 'dark_request': False},
            'queryId': get_query_id(Endpoint.CREATE_RETWEET)
        }
        return await self.base.post(
            Endpoint.CREATE_RETWEET,
            json=data,
            headers=self.base._base_headers
        )

    async def delete_retweet(self, tweet_id):
        data = {
            'variables': {'source_tweet_id': tweet_id,'dark_request': False},
            'queryId': get_query_id(Endpoint.DELETE_RETWEET)
        }
        return await self.base.post(
            Endpoint.DELETE_RETWEET,
            json=data,
            headers=self.base._base_headers
        )

    async def create_bookmark(self, tweet_id):
        variables = {'tweet_id': tweet_id}
        data = {
            'variables': variables,
            'queryId': get_query_id(Endpoint.CREATE_BOOKMARK)
        }
        return await self.base.post(
            Endpoint.CREATE_BOOKMARK,
            json=data,
            headers=self.base._base_headers
        )

    async def bookmark_tweet_to_folder(self, tweet_id, folder_id):
        variables = {
            'tweet_id': tweet_id,
            'bookmark_collection_id': folder_id
        }
        data = {
            'variables': variables,
            'queryId': get_query_id(Endpoint.CREATE_BOOKMARK)
        }
        return await self.base.post(
            Endpoint.BOOKMARK_TO_FOLDER,
            json=data,
            headers=self.base._base_headers
        )

    async def delete_bookmark(self, tweet_id):
        data = {
            'variables': {'tweet_id': tweet_id},
            'queryId': get_query_id(Endpoint.DELETE_BOOKMARK)
        }
        return await self.base.post(
            Endpoint.DELETE_BOOKMARK,
            json=data,
            headers=self.base._base_headers
        )

    async def bookmarks(self, count, cursor):
        variables = {
            'count': count,
            'includePromotedContent': True
        }
        features = FEATURES | {
            'graphql_timeline_v2_bookmark_timeline': True
        }
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({
            'variables': variables,
            'features': features
        })
        return await self.base.get(
            endpoint = Endpoint.BOOKMARKS,
            params=params,
            headers=self.base._base_headers
        )

    async def bookmark_folder_timeline(self, count, cursor, folder_id):
        variables = {
            'count': count,
            'includePromotedContent': True
        }
        endpoint = Endpoint.BOOKMARK_FOLDER_TIMELINE
        variables['bookmark_collection_id'] = folder_id
        features = BOOKMARK_FOLDER_TIMELINE_FEATURES
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({
            'variables': variables,
            'features': features
        })
        return await self.base.get(
            endpoint,
            params=params,
            headers=self.base._base_headers
        )

    async def delete_all_bookmarks(self):
        data = {
            'variables': {},
            'queryId': get_query_id(Endpoint.BOOKMARKS_ALL_DELETE)
        }
        return await self.base.post(
            Endpoint.BOOKMARKS_ALL_DELETE,
            json=data,
            headers=self.base._base_headers
        )

    async def bookmark_folders_slice(self, cursor):
        variables = {}
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({'variables': variables})
        return await self.base.get(
            Endpoint.BOOKMARK_FOLDERS_SLICE,
            params=params,
            headers=self.base._base_headers
        )

    async def edit_bookmark_folder(self, folder_id, name):
        variables = {
            'bookmark_collection_id': folder_id,
            'name': name
        }
        data = {
            'variables': variables,
            'queryId': get_query_id(Endpoint.EDIT_BOOKMARK_FOLDER)
        }
        return await self.base.post(
            Endpoint.EDIT_BOOKMARK_FOLDER,
            json=data,
            headers=self.base._base_headers
        )

    async def delete_bookmark_folder(self, folder_id):
        variables = {'bookmark_collection_id': folder_id}
        data = {
            'variables': variables,
            'queryId': get_query_id(Endpoint.DELETE_BOOKMARK_FOLDER)
        }
        return await self.base.post(
            Endpoint.DELETE_BOOKMARK_FOLDER,
            json=data,
            headers=self.base._base_headers
        )

    async def create_bookmark_folder(self, name):
        variables = {'name': name}
        data = {
            'variables': variables,
            'queryId': get_query_id(Endpoint.CREATE_BOOKMARK_FOLDER)
        }
        return await self.base.post(
            Endpoint.CREATE_BOOKMARK_FOLDER,
            json=data,
            headers=self.base._base_headers
        )

    async def _friendships(self, user_id, count, endpoint, cursor):
        variables = {
            'userId': user_id,
            'count': count,
            'includePromotedContent': False
        }
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({
            'variables': variables,
            'features': FEATURES
        })
        return await self.base.get(
            endpoint,
            params=params,
            headers=self.base._base_headers
        )

    async def followers(self, user_id, count, cursor):
        return await self._friendships(user_id, count, Endpoint.FOLLOWERS, cursor)

    async def blue_verified_followers(self, user_id, count, cursor):
        return await self._friendships(user_id, count, Endpoint.BLUE_VERIFIED_FOLLOWERS, cursor)

    async def followers_you_know(self, user_id, count, cursor):
        return await self._friendships(user_id, count, Endpoint.FOLLOWERS_YOU_KNOW, cursor)

    async def following(self, user_id, count, cursor):
        return await self._friendships(user_id, count, Endpoint.FOLLOWING, cursor)

    async def user_creator_subscriptions(self, user_id, count, cursor):
        return await self._friendships(user_id, count, Endpoint.USER_CREATOR_SUBSCRIPTIONS, cursor)

    async def user_dm_reaction_mutation_add_mutation(self, message_id, conversation_id, emoji):
        variables = {
            'messageId': message_id,
            'conversationId': conversation_id,
            'reactionTypes': ['Emoji'],
            'emojiReactions': [emoji]
        }
        data = {
            'variables': variables,
            'queryId': get_query_id(Endpoint.USER_DM_REACTION_MUTATION_ADD_MUTATION)
        }
        return await self.base.post(
            Endpoint.USER_DM_REACTION_MUTATION_ADD_MUTATION,
            json=data,
            headers=self.base._base_headers
        )

    async def user_dm_reaction_mutation_remove_mutation(self, message_id, conversation_id, emoji):
        variables = {
            'conversationId': conversation_id,
            'messageId': message_id,
            'reactionTypes': ['Emoji'],
            'emojiReactions': [emoji]
        }
        data = {
            'variables': variables,
            'queryId': get_query_id(Endpoint.USER_DM_REACTION_MUTATION_REMOVE_MUTATION)
        }
        return await self.base.post(
            Endpoint.USER_DM_REACTION_MUTATION_REMOVE_MUTATION,
            json=data,
            headers=self.base._base_headers
        )

    async def dm_message_delete_mutation(self, message_id):
        data = {
            'variables': {
                'messageId': message_id
            },
            'queryId': get_query_id(Endpoint.DM_MESSAGE_DELETE_MUTATION)
        }
        return await self.base.post(
            Endpoint.DM_MESSAGE_DELETE_MUTATION,
            json=data,
            headers=self.base._base_headers
        )

    async def add_members_to_group(self, group_id, user_ids):
        data = {
            'variables': {
                'addedParticipants': user_ids,
                'conversationId': group_id
            },
            'queryId': get_query_id(Endpoint.ADD_PARTICIPANTS_MUTATION)
        }
        return await self.base.post(
            Endpoint.ADD_PARTICIPANTS_MUTATION,
            json=data,
            headers=self.base._base_headers
        )

    async def create_list(self, name, description, is_private):
        variables = {
            'isPrivate': is_private,
            'name': name,
            'description': description
        }
        data = {
            'variables': variables,
            'features': LIST_FEATURES,
            'queryId': get_query_id(Endpoint.CREATE_LIST)
        }
        return await self.base.post(
            Endpoint.CREATE_LIST,
            json=data,
            headers=self.base._base_headers
        )

    async def edit_list_banner(self, list_id, media_id):
        variables = {
            'listId': list_id,
            'mediaId': media_id
        }
        data = {
            'variables': variables,
            'features': LIST_FEATURES,
            'queryId': get_query_id(Endpoint.EDIT_LIST_BANNER)
        }
        return await self.base.post(
            Endpoint.EDIT_LIST_BANNER,
            json=data,
            headers=self.base._base_headers
        )

    async def delete_list_banner(self, list_id):
        data = {
            'variables': {
                'listId': list_id
            },
            'features': LIST_FEATURES,
            'queryId': get_query_id(Endpoint.DELETE_LIST_BANNER)
        }
        return await self.base.post(
            Endpoint.DELETE_LIST_BANNER,
            json=data,
            headers=self.base._base_headers
        )

    async def update_list(self, list_id, name, description, is_private):
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
            'queryId': get_query_id(Endpoint.UPDATE_LIST)
        }
        return await self.base.post(
            Endpoint.UPDATE_LIST,
            json=data,
            headers=self.base._base_headers
        )

    async def list_add_member(self, list_id, user_id):
        variables = {
            'listId': list_id,
            'userId': user_id
        }
        data = {
            'variables': variables,
            'features': LIST_FEATURES,
            'queryId': get_query_id(Endpoint.LIST_ADD_MEMBER)
        }
        return await self.base.post(
            Endpoint.LIST_ADD_MEMBER,
            json=data,
            headers=self.base._base_headers
        )

    async def list_remove_member(self, list_id, user_id):
        variables = {
            'listId': list_id,
            'userId': user_id
        }
        data = {
            'variables': variables,
            'features': LIST_FEATURES,
            'queryId': get_query_id(Endpoint.LIST_REMOVE_MEMBER)
        }
        return await self.base.post(
            Endpoint.LIST_REMOVE_MEMBER,
            json=data,
            headers=self.base._base_headers
        )

    async def list_management_pace_timeline(self, count, cursor):
        variables = {'count': count}
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({
            'variables': variables,
            'features': FEATURES
        })
        return await self.base.get(
            Endpoint.LIST_MANAGEMENT_PACE_TIMELINE,
            params=params,
            headers=self.base._base_headers
        )

    async def list_by_rest_id(self, list_id):
        params = flatten_params({
            'variables': {'listId': list_id},
            'features': LIST_FEATURES
        })
        return await self.base.get(
            Endpoint.LIST_BY_REST_ID,
            params=params,
            headers=self.base._base_headers
        )

    async def list_latest_tweets_timeline(self, list_id, count, cursor):
        variables = {'listId': list_id, 'count': count}
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({
            'variables': variables,
            'features': FEATURES
        })
        return await self.base.get(
            Endpoint.LIST_LATEST_TWEETS_TIMELINE,
            params=params,
            headers=self.base._base_headers
        )

    async def _list_users(self, endpoint, list_id, count, cursor):
        variables = {'listId': list_id, 'count': count}
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({
            'variables': variables,
            'features': FEATURES
        })
        return await self.base.get(
            endpoint,
            params=params,
            headers=self.base._base_headers
        )

    async def list_members(self, list_id, count, cursor):
        return self._list_users(Endpoint.LIST_MEMBERS, list_id, count, cursor)

    async def list_subscribers(self, list_id, count, cursor):
        return self._list_users(Endpoint.LIST_SUBSCRIBERS, list_id, count, cursor)

    async def search_community(self, query, cursor):
        variables = {'query': query}
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({
            'variables': variables
        })
        return await self.base.get(
            Endpoint.SEARCH_COMMUNITY,
            params=params,
            headers=self.base._base_headers
        )

    async def community_query(self, community_id):
        params = flatten_params({
            'variables': {'communityId': community_id},
            'features': {
                'c9s_list_members_action_api_enabled':False,
                'c9s_superc9s_indication_enabled':False
            }
        })
        return await self.base.get(
            Endpoint.COMMUNITY_QUERY,
            params=params,
            headers=self.base._base_headers
        )

    async def community_media_timeline(self, community_id, count, cursor):
        variables = {
            'communityId': community_id,
            'count': count,
            'withCommunity': True
        }
        if cursor is not None:
            variables['cursor'] = cursor

        params = flatten_params({
            'variables': variables,
            'features': COMMUNITY_TWEETS_FEATURES
        })
        return await self.base.get(
            Endpoint.COMMUNITY_MEDIA_TIMELINE,
            params=params,
            headers=self.base._base_headers
        )

    async def community_tweets_timeline(self, community_id, ranking_mode, count, cursor):
        variables = {
            'communityId': community_id,
            'count': count,
            'withCommunity': True,
            'rankingMode': ranking_mode
        }
        if cursor is not None:
            variables['cursor'] = cursor

        params = flatten_params({
            'variables': variables,
            'features': COMMUNITY_TWEETS_FEATURES
        })
        return await self.base.get(
            Endpoint.COMMUNITY_TWEETS_TIMELINE,
            params=params,
            headers=self.base._base_headers
        )

    async def communities_main_page_timeline(self, count, cursor):
        variables = {
            'count': count,
            'withCommunity': True
        }
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({
            'variables': variables,
            'features': COMMUNITY_TWEETS_FEATURES
        })
        return await self.base.get(
            Endpoint.COMMUNITIES_MAIN_PAGE_TIMELINE,
            params=params,
            headers=self.base._base_headers
        )

    async def join_community(self, community_id):
        data = {
            'variables': {
                'communityId': community_id
            },
            'features': JOIN_COMMUNITY_FEATURES,
            'queryId': get_query_id(Endpoint.JOIN_COMMUNITY)
        }
        return await self.base.post(
            Endpoint.JOIN_COMMUNITY,
            json=data,
            headers=self.base._base_headers
        )

    async def leave_community(self, community_id):
        data = {
            'variables': {
                'communityId': community_id
            },
            'features': JOIN_COMMUNITY_FEATURES,
            'queryId': get_query_id(Endpoint.LEAVE_COMMUNITY)
        }
        return await self.base.post(
            Endpoint.LEAVE_COMMUNITY,
            json=data,
            headers=self.base._base_headers
        )

    async def request_to_join_community(self, community_id, answer):
        data = {
            'variables': {
                'communityId': community_id,
                'answer': '' if answer is None else answer
            },
            'features': JOIN_COMMUNITY_FEATURES,
            'queryId': get_query_id(Endpoint.REQUEST_TO_JOIN_COMMUNITY)
        }
        return await self.base.post(
            Endpoint.REQUEST_TO_JOIN_COMMUNITY,
            json=data,
            headers=self.base._base_headers
        )

    async def _get_community_users(self, endpoint, community_id, count, cursor):
        variables = {
            'communityId': community_id,
            'count': count
        }
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({
            'variables': variables,
            'features': {
                'responsive_web_graphql_timeline_navigation_enabled': True
            }
        })
        return await self.base.get(
            endpoint,
            params=params,
            headers=self.base._base_headers
        )

    async def members_slice_timeline_query(self, community_id, count, cursor):
        return await self._get_community_users(Endpoint.MEMBERS_SLICE_TIMELINE_QUERY, community_id, count, cursor)

    async def moderators_slice_timeline_query(self, community_id, count, cursor):
        return await self._get_community_users(Endpoint.MODERATORS_SLICE_TIMELINE_QUERY, community_id, count, cursor)

    async def community_tweet_search_module_query(self, community_id, query, count, cursor):
        variables = {
            "count": count,
            "query": query,
            "communityId": community_id,
            "includePromotedContent": False,
            "withBirdwatchNotes": True,
            "withVoice": False,
            "isListMemberTargetUserId": "0",
            "withCommunity": False,
            "withSafetyModeUserFields": True
        }
        if cursor is not None:
            variables['cursor'] = cursor
        params = flatten_params({
            'variables': variables,
            'features': COMMUNITY_TWEETS_FEATURES
        })
        return await self.base.get(
            Endpoint.COMMUNITY_TWEET_SEARCH_MODULE_QUERY,
            params=params,
            headers=self.base._base_headers
        )
