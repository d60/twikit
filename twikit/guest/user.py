from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal

from ..utils import Result, timestamp_to_datetime

if TYPE_CHECKING:
    from .client import GuestClient
    from .tweet import Tweet


class User:
    """
    Attributes
    ----------
    id : :class:`str`
        The unique identifier of the user.
    created_at : :class:`str`
        The date and time when the user account was created.
    name : :class:`str`
        The user's name.
    screen_name : :class:`str`
        The user's screen name.
    profile_image_url : :class:`str`
        The URL of the user's profile image (HTTPS version).
    profile_banner_url : :class:`str`
        The URL of the user's profile banner.
    url : :class:`str`
        The user's URL.
    location : :class:`str`
        The user's location information.
    description : :class:`str`
        The user's profile description.
    description_urls : :class:`list`
        URLs found in the user's profile description.
    urls : :class:`list`
        URLs associated with the user.
    pinned_tweet_ids : :class:`str`
        The IDs of tweets that the user has pinned to their profile.
    is_blue_verified : :class:`bool`
        Indicates if the user is verified with a blue checkmark.
    verified : :class:`bool`
        Indicates if the user is verified.
    possibly_sensitive : :class:`bool`
        Indicates if the user's content may be sensitive.
    can_media_tag : :class:`bool`
        Indicates whether the user can be tagged in media.
    want_retweets : :class:`bool`
        Indicates if the user wants retweets.
    default_profile : :class:`bool`
        Indicates if the user has the default profile.
    default_profile_image : :class:`bool`
        Indicates if the user has the default profile image.
    has_custom_timelines : :class:`bool`
        Indicates if the user has custom timelines.
    followers_count : :class:`int`
        The count of followers.
    fast_followers_count : :class:`int`
        The count of fast followers.
    normal_followers_count : :class:`int`
        The count of normal followers.
    following_count : :class:`int`
        The count of users the user is following.
    favourites_count : :class:`int`
        The count of favorites or likes.
    listed_count : :class:`int`
        The count of lists the user is a member of.
    media_count : :class:`int`
        The count of media items associated with the user.
    statuses_count : :class:`int`
        The count of tweets.
    is_translator : :class:`bool`
        Indicates if the user is a translator.
    translator_type : :class:`str`
        The type of translator.
    profile_interstitial_type : :class:`str`
        The type of profile interstitial.
    withheld_in_countries : list[:class:`str`]
        Countries where the user's content is withheld.
    """

    def __init__(self, client: GuestClient, data: dict) -> None:
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
        self.protected: bool = legacy.get('protected', False)

    @property
    def created_at_datetime(self) -> datetime:
        return timestamp_to_datetime(self.created_at)

    async def get_tweets(self, tweet_type: Literal['Tweets'] = 'Tweets', count: int = 40) -> list[Tweet]:
        """
        Retrieves the user's tweets.

        Parameters
        ----------
        tweet_type : {'Tweets'}, default='Tweets'
            The type of tweets to retrieve.
        count : :class:`int`, default=40
            The number of tweets to retrieve.

        Returns
        -------
        list[:class:`.tweet.Tweet`]
            A list of `Tweet` objects.

        Examples
        --------
        >>> user = await client.get_user_by_screen_name('example_user')
        >>> tweets = await user.get_tweets()
        >>> for tweet in tweets:
        ...    print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        ...
        """
        return await self._client.get_user_tweets(self.id, tweet_type, count)

    async def get_highlights_tweets(self, count: int = 20, cursor: str | None = None) -> Result[Tweet]:
        """
        Retrieves highlighted tweets from the user's timeline.

        Parameters
        ----------
        count : :class:`int`, default=20
            The number of tweets to retrieve.

        Returns
        -------
        Result[:class:`.tweet.Tweet`]
            An instance of the `Result` class containing the highlighted tweets.

        Examples
        --------
        >>> result = await user.get_highlights_tweets()
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
        return await self._client.get_user_highlights_tweets(self.id, count, cursor)

    async def update(self) -> None:
        new = await self._client.get_user_by_id(self.id)
        self.__dict__.update(new.__dict__)

    def __repr__(self) -> str:
        return f'<User id="{self.id}">'

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, User) and self.id == __value.id

    def __ne__(self, __value: object) -> bool:
        return not self == __value
