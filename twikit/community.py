from __future__ import annotations

from typing import TYPE_CHECKING, Literal, NamedTuple

from .tweet import Tweet
from .user import User
from .utils import Result, b64_to_str

if TYPE_CHECKING:
    from .client.client import Client


class CommunityCreator(NamedTuple):
    id: str
    screen_name: str
    verified: bool


class CommunityRule(NamedTuple):
    id: str
    name: str


class CommunityMember:
    def __init__(self, client: Client, data: dict) -> None:
        self._client = client
        self.id: str = data['rest_id']

        self.community_role: str = data['community_role']
        self.super_following: bool = data['super_following']
        self.super_follow_eligible: bool = data['super_follow_eligible']
        self.super_followed_by: bool = data['super_followed_by']
        self.smart_blocking: bool = data['smart_blocking']
        self.is_blue_verified: bool = data['is_blue_verified']

        legacy = data['legacy']
        self.screen_name: str = legacy['screen_name']
        self.name: str = legacy['name']
        self.follow_request_sent: bool = legacy['follow_request_sent']
        self.protected: bool = legacy['protected']
        self.following: bool = legacy['following']
        self.followed_by: bool = legacy['followed_by']
        self.blocking: bool = legacy['blocking']
        self.profile_image_url_https: str = legacy['profile_image_url_https']
        self.verified: bool = legacy['verified']

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, CommunityMember) and self.id == __value.id

    def __ne__(self, __value: object) -> bool:
        return not self == __value

    def __repr__(self) -> str:
        return f'<CommunityMember id="{self.id}">'


class Community:
    """
    Attributes
    ----------
    id : :class:`str`
        The ID of the community.
    name : :class:`str`
        The name of the community.
    member_count : :class:`int`
        The count of members in the community.
    is_nsfw : :class:`bool`
        Indicates if the community is NSFW.
    members_facepile_results : list[:class:`str`]
        The profile image URLs of members.
    banner : :class:`dict`
        The banner information of the community.
    is_member : :class:`bool`
        Indicates if the user is a member of the community.
    role : :class:`str`
        The role of the user in the community.
    description : :class:`str`
        The description of the community.
    creator : :class:`User` | :class:`CommunityCreator`
        The creator of the community.
    admin : :class:`User`
        The admin of the community.
    join_policy : :class:`str`
        The join policy of the community.
    created_at : :class:`int`
        The timestamp of the community's creation.
    invites_policy : :class:`str`
        The invites policy of the community.
    is_pinned : :class:`bool`
        Indicates if the community is pinned.
    rules : list[:class:`CommunityRule`]
        The rules of the community.
    """

    def __init__(self, client: Client, data: dict) -> None:
        self._client = client
        self.id: str = data['rest_id']

        self.name: str = data['name']
        self.member_count: int = data['member_count']
        self.is_nsfw: bool = data['is_nsfw']

        self.members_facepile_results: list[str] = [
            i['result']['legacy']['profile_image_url_https']
            for i in data['members_facepile_results']
        ]
        self.banner: dict = data['default_banner_media']['media_info']

        self.is_member: bool = data.get('is_member')
        self.role: str = data.get('role')
        self.description: str = data.get('description')

        if 'creator_results' in data:
            creator = data['creator_results']['result']
            if 'rest_id' in creator:
                self.creator = User(client, creator)
            else:
                self.creator = CommunityCreator(
                    b64_to_str(creator['id']).removeprefix('User:'),
                    creator['legacy']['screen_name'],
                    creator['legacy']['verified']
                )
        else:
            self.creator = None

        if 'admin_results' in data:
            admin = data['admin_results']['result']
            self.admin = User(client, admin)
        else:
            self.admin = None

        self.join_policy: str = data.get('join_policy')
        self.created_at: int = data.get('created_at')
        self.invites_policy: str = data.get('invites_policy')
        self.is_pinned: bool = data.get('is_pinned')

        if 'rules' in data:
            self.rules: list = [
                CommunityRule(i['rest_id'], i['name']) for i in data['rules']
            ]
        else:
            self.rules = None

    async def get_tweets(
        self,
        tweet_type: Literal['Top', 'Latest', 'Media'],
        count: int = 40,
        cursor: str | None = None
    ) -> Result[Tweet]:
        """
        Retrieves tweets from the community.

        Parameters
        ----------
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
        >>> tweets = await community.get_tweets('Latest')
        >>> for tweet in tweets:
        ...     print(tweet)
        <Tweet id="...">
        <Tweet id="...">
        ...
        >>> more_tweets = await tweets.next()  # Retrieve more tweets
        """
        return await self._client.get_community_tweets(
            self.id,
            tweet_type,
            count,
            cursor
        )

    async def join(self) -> Community:
        """
        Join the community.
        """
        return await self._client.join_community(self.id)

    async def leave(self) -> Community:
        """
        Leave the community.
        """
        return await self._client.leave_community(self.id)

    async def request_to_join(self, answer: str | None = None) -> Community:
        """
        Request to join the community.
        """
        return await self._client.request_to_join_community(self.id, answer)

    async def get_members(
        self, count: int = 20, cursor: str | None = None
    ) -> Result[CommunityMember]:
        """
        Retrieves members of the community.

        Parameters
        ----------
        count : :class:`int`, default=20
            The number of members to retrieve.

        Returns
        -------
        Result[:class:`CommunityMember`]
            List of retrieved members.
        """
        return await self._client.get_community_members(
            self.id,
            count,
            cursor
        )

    async def get_moderators(
        self, count: int = 20, cursor: str | None = None
    ) -> Result[CommunityMember]:
        """
        Retrieves moderators of the community.

        Parameters
        ----------
        count : :class:`int`, default=20
            The number of moderators to retrieve.

        Returns
        -------
        Result[:class:`CommunityMember`]
            List of retrieved moderators.
        """
        return await self._client.get_community_moderators(
            self.id,
            count,
            cursor
        )

    async def search_tweet(
        self,
        query: str,
        count: int = 20,
        cursor: str | None = None
    )-> Result[Tweet]:
        """Searchs tweets in the community.

        Parameters
        ----------
        query : :class:`str`
            The search query.
        count : :class:`int`, default=20
            The number of tweets to retrieve.

        Returns
        -------
        Result[:class:`Tweet`]
            List of retrieved tweets.
        """
        return await self._client.search_community_tweet(
            self.id,
            query,
            count,
            cursor
        )

    async def update(self) -> None:
        new = await self._client.get_community(self.id)
        self.__dict__.update(new.__dict__)

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, Community) and self.id == __value.id

    def __ne__(self, __value: object) -> bool:
        return not self == __value

    def __repr__(self) -> str:
        return f'<Community id="{self.id}">'
