from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from httpx import Response

    from .client import Client
    from .message import Message
    from .tweet import Tweet
    from .utils import Result


class User:
    """
    Attributes
    ----------
    id : str
        The unique identifier of the user.
    created_at : str
        The date and time when the user account was created.
    name : str
        The user's name.
    screen_name : str
        The user's screen name.
    profile_image_url : str
        The URL of the user's profile image (HTTPS version).
    profile_banner_url : str
        The URL of the user's profile banner.
    url : str
        The user's URL.
    location : str
        The user's location information.
    description : str
        The user's profile description.
    description_urls : list
        URLs found in the user's profile description.
    urls : list
        URLs associated with the user.
    pinned_tweet_ids : str
        The IDs of tweets that the user has pinned to their profile.
    is_blue_verified : bool
        Indicates if the user is verified with a blue checkmark.
    verified : bool
        Indicates if the user is verified.
    possibly_sensitive : bool
        Indicates if the user's content may be sensitive.
    can_dm : bool
        Indicates whether the user can receive direct messages.
    can_media_tag : bool
        Indicates whether the user can be tagged in media.
    want_retweets : bool
        Indicates if the user wants retweets.
    default_profile : bool
        Indicates if the user has the default profile.
    default_profile_image : bool
        Indicates if the user has the default profile image.
    has_custom_timelines : bool
        Indicates if the user has custom timelines.
    followers_count : int
        The count of followers.
    fast_followers_count : int
        The count of fast followers.
    normal_followers_count : int
        The count of normal followers.
    following_count : int
        The count of users the user is following.
    favourites_count : int
        The count of favorites or likes.
    listed_count : int
        The count of lists the user is a member of.
    media_count : int
        The count of media items associated with the user.
    statuses_count : int
        The count of tweets.
    is_translator : bool
        Indicates if the user is a translator.
    translator_type : str
        The type of translator.
    profile_interstitial_type : str
        The type of profile interstitial.
    withheld_in_countries : list[str]
        Countries where the user's content is withheld.
    """

    def __init__(self, client: Client, data: dict) -> None:
        self._client = client
        legacy = data['legacy']

        self.id: str = data['rest_id']
        self.created_at: str = legacy['created_at']
        self.name: str = legacy['name']
        self.screen_name: str = legacy['screen_name']
        self.profile_image_url: str = legacy['profile_image_url_https']
        self.profile_banner_url: str = legacy.get('profile_banner_url')
        self.url: str = legacy.get('url')
        self.location: str = legacy['location']
        self.description: str = legacy['description']
        self.description_urls: list = legacy['entities']['description']['urls']
        self.urls: list = legacy['entities'].get('url', {}).get('urls')
        self.pinned_tweet_ids: list[str] = legacy['pinned_tweet_ids_str']
        self.is_blue_verified: bool = data['is_blue_verified']
        self.verified: bool = legacy['verified']
        self.possibly_sensitive: bool = legacy['possibly_sensitive']
        self.can_dm: bool = legacy['can_dm']
        self.can_media_tag: bool = legacy['can_media_tag']
        self.want_retweets: bool = legacy['want_retweets']
        self.default_profile: bool = legacy['default_profile']
        self.default_profile_image: bool = legacy['default_profile_image']
        self.has_custom_timelines: bool = legacy['has_custom_timelines']
        self.followers_count: int = legacy['followers_count']
        self.fast_followers_count: int = legacy['fast_followers_count']
        self.normal_followers_count: int = legacy['normal_followers_count']
        self.following_count: int = legacy['friends_count']
        self.favourites_count: int = legacy['favourites_count']
        self.listed_count: int = legacy['listed_count']
        self.media_count = legacy['media_count']
        self.statuses_count: int = legacy['statuses_count']
        self.is_translator: bool = legacy['is_translator']
        self.translator_type: str = legacy['translator_type']
        self.withheld_in_countries: list[str] = legacy['withheld_in_countries']

    def get_tweets(
        self,
        tweet_type: Literal['Tweets', 'Replies', 'Media', 'Likes'],
        count: int = 40,
    ) -> Result[Tweet]:
        """
        Retrieves the user's tweets.

        Parameters
        ----------
        tweet_type : {'Tweets', 'Replies', 'Media', 'Likes'}
            The type of tweets to retrieve.
        count : int, default=40
            The number of tweets to retrieve.

        Returns
        -------
        Result[Tweet]
            A Result object containing a list of `Tweet` objects.

        Examples
        --------
        >>> user = client.get_user_by_screen_name('example_user')
        >>> tweets = user.get_tweets('Tweets', count=20)
        >>> for tweet in tweets:
        ...    print(tweet)
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
        return self._client.get_user_tweets(self.id, tweet_type, count)

    def follow(self) -> Response:
        """
        Follows the user.

        Returns
        -------
        httpx.Response
            Response returned from twitter api.

        See Also
        --------
        Client.follow_user
        """
        return self._client.follow_user(self.id)

    def unfollow(self) -> Response:
        """
        Unfollows the user.

        Returns
        -------
        httpx.Response
            Response returned from twitter api.

        See Also
        --------
        Client.unfollow_user
        """
        return self._client.unfollow_user(self.id)

    def block(self) -> Response:
        """
        Blocks a user.

        Parameters
        ----------
        user_id : str
            The ID of the user to block.

        Returns
        -------
        httpx.Response
            Response returned from twitter api.

        See Also
        --------
        .unblock
        """
        return self._client.block_user(self.id)

    def unblock(self) -> Response:
        """
        Unblocks a user.

        Parameters
        ----------
        user_id : str
            The ID of the user to unblock.

        Returns
        -------
        httpx.Response
            Response returned from twitter api.

        See Also
        --------
        .block
        """
        return self._client.unblock_user(self.id)

    def mute(self) -> Response:
        """
        Mutes a user.

        Parameters
        ----------
        user_id : str
            The ID of the user to mute.

        Returns
        -------
        httpx.Response
            Response returned from twitter api.

        See Also
        --------
        .unmute
        """
        return self._client.mute_user(self.id)

    def unmute(self) -> Response:
        """
        Unmutes a user.

        Parameters
        ----------
        user_id : str
            The ID of the user to unmute.

        Returns
        -------
        httpx.Response
            Response returned from twitter api.

        See Also
        --------
        .mute
        """
        return self._client.unmute_user(self.id)

    def get_followers(self, count: int = 20) -> list[User]:
        """
        Retrieves a list of followers for the user.

        Parameters
        ----------
        count : int, default=20
            The number of followers to retrieve.

        Returns
        -------
        list[User]
            A list of User objects representing the followers.

        See Also
        --------
        Client.get_user_followers
        """
        return self._client.get_user_followers(self.id, count)

    def get_verified_followers(self, count: int = 20) -> list[User]:
        """
        Retrieves a list of verified followers for the user.

        Parameters
        ----------
        count : int, default=20
            The number of verified followers to retrieve.

        Returns
        -------
        list[User]
            A list of User objects representing the verified followers.

        See Also
        --------
        Client.get_user_verified_followers
        """
        return self._client.get_user_verified_followers(self.id, count)

    def get_followers_you_know(self, count: int = 20) -> list[User]:
        """
        Retrieves a list of followers whom the user might know.

        Parameters
        ----------
        count : int, default=20
            The number of followers you might know to retrieve.

        Returns
        -------
        list[User]
            A list of User objects representing the followers you might know.

        See Also
        --------
        Client.get_user_followers_you_know
        """
        return self._client.get_user_followers_you_know(self.id, count)

    def get_following(self, count: int = 20) -> list[User]:
        """
        Retrieves a list of users whom the user is following.

        Parameters
        ----------
        count : int, default=20
            The number of following users to retrieve.

        Returns
        -------
        list[User]
            A list of User objects representing the users being followed.

        See Also
        --------
        Client.get_user_following
        """
        return self._client.get_user_following(self.id, count)

    def get_subscriptions(self, count: int = 20) -> list[User]:
        """
        Retrieves a list of users whom the user is subscribed to.

        Parameters
        ----------
        count : int, default=20
            The number of subscriptions to retrieve.

        Returns
        -------
        list[User]
            A list of User objects representing the subscribed users.

        See Also
        --------
        Client.get_user_subscriptions
        """
        return self._client.get_user_subscriptions(self.id, count)

    def send_dm(
        self, text: str, media_id: str = None, reply_to = None
    ) -> Message:
        """
        Send a direct message to the user.

        Parameters
        ----------
        text : str
            The text content of the direct message.
        media_id : str, default=None
            The media ID associated with any media content
            to be included in the message.
            Media ID can be received by using the :func:`.upload_media` method.
        reply_to : str, default=None
            Message ID to reply to.

        Returns
        -------
        Message
            `Message` object containing information about the message sent.

        Examples
        --------
        >>> # send DM with media
        >>> media_id = client.upload_media('image.png', 0)
        >>> message = user.send_dm('text', media_id)
        >>> print(message)
        <Message id='...'>

        See Also
        --------
        Client.upload_media
        Client.send_dm
        """
        return self._client.send_dm(self.id, text, media_id, reply_to)

    def get_dm_history(self, max_id: str = None) -> Result[Message]:
        """
        Retrieves the DM conversation history with the user.

        Parameters
        ----------
        max_id : str, default=None
            If specified, retrieves messages older than the specified max_id.

        Returns
        -------
        Result[Message]
            A Result object containing a list of Message objects representing
            the DM conversation history.

        Examples
        --------
        >>> messages = user.get_dm_history()
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
        return self._client.get_dm_history(self.id, max_id)

    def __repr__(self) -> str:
        return f'<User id="{self.id}">'

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, User) and self.id == __value.id

    def __ne__(self, __value: object) -> bool:
        return not self == __value
