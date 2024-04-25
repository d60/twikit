from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal

from twikit.utils import timestamp_to_datetime

if TYPE_CHECKING:
    from httpx import Response

    from twikit.client import Client
    from twikit.tweet import Tweet
    from twikit.user import User
    from twikit.utils import Result


class List:
    """
    Class representing a Twitter List.

    Attributes
    ----------
    id : :class:`str`
        The unique identifier of the List.
    created_at : :class:`int`
        The timestamp when the List was created.
    default_banner : :class:`dict`
        Information about the default banner of the List.
    banner : :class:`dict`
        Information about the banner of the List. If custom banner is not set,
        it defaults to the default banner.
    description : :class:`str`
        The description of the List.
    following : :class:`bool`
        Indicates if the authenticated user is following the List.
    is_member : :class:`bool`
        Indicates if the authenticated user is a member of the List.
    member_count : :class:`int`
        The number of members in the List.
    mode : {'Private', 'Public'}
        The mode of the List, either 'Private' or 'Public'.
    muting : :class:`bool`
        Indicates if the authenticated user is muting the List.
    name : :class:`str`
        The name of the List.
    pinning : :class:`bool`
        Indicates if the List is pinned.
    subscriber_count : :class:`int`
        The number of subscribers to the List.
    """

    def __init__(self, client: Client, data: dict) -> None:
        self._client = client

        self.id: str = data['id_str']
        self.created_at: int = data['created_at']
        self.default_banner: dict = data['default_banner_media']['media_info']

        self.banner: dict = self.default_banner
        if 'custom_banner_media' in data:
            self.banner = data['custom_banner_media']['media_info']

        self.description: str = data['description']
        self.following: bool = data['following']
        self.is_member: bool = data['is_member']
        self.member_count: bool = data['member_count']
        self.mode: Literal['Private', 'Public'] = data['mode']
        self.muting: bool = data['muting']
        self.name: str = data['name']
        self.pinning: bool = data['pinning']
        self.subscriber_count: int = data['subscriber_count']

    @property
    def created_at_datetime(self) -> datetime:
        return timestamp_to_datetime(str(self.created_at))

    def edit_banner(self, media_id: str) -> Response:
        """
        Edit the banner image of the list.

        Parameters
        ----------
        media_id : :class:`str`
            The ID of the media to use as the new banner image.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> media_id = client.upload_media('image.png')
        >>> media.edit_banner(media_id)
        """
        return self._client.edit_list_banner(self.id, media_id)

    def delete_banner(self) -> Response:
        """
        Deletes the list banner.
        """
        return self._client.delete_list_banner(self.id)

    def edit(
        self,
        name: str | None = None,
        description: str | None = None,
        is_private: bool | None = None,
    ) -> List:
        """
        Edits list information.

        Parameters
        ----------
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
        >>> list.edit('new name', 'new description', True)
        """
        return self._client.edit_list(self.id, name, description, is_private)

    def add_member(self, user_id: str) -> Response:
        """
        Adds a member to the list.
        """
        return self._client.add_list_member(self.id, user_id)

    def remove_member(self, user_id: str) -> Response:
        """
        Removes a member from the list.
        """
        return self._client.remove_list_member(self.id, user_id)

    def get_tweets(self, count: int = 20, cursor: str | None = None) -> Result[Tweet]:
        """
        Retrieves tweets from the list.

        Parameters
        ----------
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
        >>> tweets = list.get_tweets()
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
        return self._client.get_list_tweets(self.id, count, cursor)

    def get_members(self, count: int = 20, cursor: str | None = None) -> Result[User]:
        """Retrieves members of the list.

        Parameters
        ----------
        count : :class:`int`, default=20
            Number of members to retrieve.

        Returns
        -------
        Result[:class:`User`]
            Members of the list

        Examples
        --------
        >>> members = list_.get_members()
        >>> for member in members:
        ...     print(member)
        <User id="...">
        <User id="...">
        ...
        ...
        >>> more_members = members.next()  # Retrieve more members
        """
        return self._client.get_list_members(self.id, count, cursor)

    def get_subscribers(self, count: int = 20, cursor: str | None = None) -> Result[User]:
        """Retrieves subscribers of the list.

        Parameters
        ----------
        count : :class:`int`, default=20
            Number of subscribers to retrieve.

        Returns
        -------
        Result[:class:`User`]
            Subscribers of the list

        Examples
        --------
        >>> subscribers = list_.get_subscribers()
        >>> for subscriber in subscribers:
        ...     print(subscriber)
        <User id="...">
        <User id="...">
        ...
        ...
        >>> more_subscribers = subscribers.next()  # Retrieve more subscribers
        """
        return self._client.get_list_subscribers(self.id, count, cursor)

    def update(self) -> None:
        new = self._client.get_list(self.id)
        self.__dict__.update(new.__dict__)

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, List) and self.id == __value.id

    def __ne__(self, __value: object) -> bool:
        return not self == __value

    def __repr__(self) -> str:
        return f'<List id="{self.id}">'
