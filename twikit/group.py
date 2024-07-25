from __future__ import annotations

from typing import TYPE_CHECKING

from .message import Message
from .user import User
from .utils import build_user_data

if TYPE_CHECKING:
    from httpx import Response

    from .client.client import Client
    from .utils import Result


class Group:
    """
    Represents a group.

    Attributes
    ----------
    id : :class:`str`
        The ID of the group.
    name : :class:`str` | None
        The name of the group.
    members : list[:class:`str`]
        Member IDs
    """
    def __init__(self, client: Client, group_id: str, data: dict) -> None:
        self._client = client
        self.id = group_id

        conversation_timeline = data["conversation_timeline"]
        self.name: str | None = (
            conversation_timeline["conversations"][group_id]["name"]
            if len(conversation_timeline["conversations"].keys()) > 0
            else None
        )

        members = conversation_timeline["users"].values()
        self.members: list[User] = [User(client, build_user_data(i)) for i in members]

    async def get_history(
        self, max_id: str | None = None
    ) -> Result[GroupMessage]:
        """
        Retrieves the DM conversation history in the group.

        Parameters
        ----------
        max_id : :class:`str`, default=None
            If specified, retrieves messages older than the specified max_id.

        Returns
        -------
        Result[:class:`GroupMessage`]
            A Result object containing a list of GroupMessage objects
            representing the DM conversation history.

        Examples
        --------
        >>> messages = await group.get_history()
        >>> for message in messages:
        >>>     print(message)
        <GroupMessage id="...">
        <GroupMessage id="...">
        ...
        ...

        >>> more_messages = await messages.next()  # Retrieve more messages
        >>> for message in more_messages:
        >>>     print(message)
        <GroupMessage id="...">
        <GroupMessage id="...">
        ...
        ...
        """
        return await self._client.get_group_dm_history(self.id, max_id)

    async def add_members(self, user_ids: list[str]) -> Response:
        """Adds members to the group.

        Parameters
        ----------
        user_ids : list[:class:`str`]
            List of IDs of users to be added.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> members = ['...']
        >>> await group.add_members(members)
        """
        return await self._client.add_members_to_group(self.id, user_ids)

    async def change_name(self, name: str) -> Response:
        """Changes group name

        Parameters
        ----------
        name : :class:`str`
            New name.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.
        """
        return await self._client.change_group_name(self.id, name)

    async def send_message(
        self,
        text: str,
        media_id: str | None = None,
        reply_to: str | None = None
    ) -> GroupMessage:
        """
        Sends a message to the group.

        Parameters
        ----------
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
            `Message` object containing information about the message sent.

        Examples
        --------
        >>> # send DM with media
        >>> group_id = '000000000'
        >>> media_id = await client.upload_media('image.png')
        >>> message = await group.send_message('text', media_id)
        >>> print(message)
        <GroupMessage id='...'>
        """
        return await self._client.send_dm_to_group(
            self.id, text, media_id, reply_to
        )

    async def update(self) -> None:
        new = await self._client.get_group(self.id)
        self.__dict__.update(new.__dict__)

    def __repr__(self) -> str:
        return f'<Group id="{self.id}">'


class GroupMessage(Message):
    """
    Represents a direct message.

    Attributes
    ----------
    id : :class:`str`
        The ID of the message.
    time : :class:`str`
        The timestamp of the message.
    text : :class:`str`
        The text content of the message.
    attachment : :class:`str`
        The media URL associated with any attachment in the message.
    group_id : :class:`str`
        The ID of the group.
    """
    def __init__(
        self,
        client: Client,
        data: dict,
        sender_id: str,
        group_id: str
    ) -> None:
        super().__init__(client, data, sender_id, None)
        self.group_id = group_id

    async def group(self) -> Group:
        """
        Gets the group to which the message was sent.
        """
        return await self._client.get_group(self.group_id)

    async def reply(
        self, text: str, media_id: str | None = None
    ) -> GroupMessage:
        """Replies to the message.

        Parameters
        ----------
        text : :class:`str`
            The text content of the direct message.
        media_id : :class:`str`, default=None
            The media ID associated with any media content
            to be included in the message.
            Media ID can be received by using the :func:`.upload_media` method.

        Returns
        -------
        :class:`Message`
            `GroupMessage` object containing information about
            the message sent.

        See Also
        --------
        Client.send_dm_to_group
        """
        return await self._client.send_dm_to_group(
            self.group_id, text, media_id, self.id
        )

    async def add_reaction(self, emoji: str) -> Response:
        """
        Adds a reaction to the message.

        Parameters
        ----------
        emoji : :class:`str`
            The emoji to be added as a reaction.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.
        """
        return await self._client.add_reaction_to_message(
            self.id, self.group_id, emoji
        )

    async def remove_reaction(self, emoji: str) -> Response:
        """
        Removes a reaction from the message.

        Parameters
        ----------
        emoji : :class:`str`
            The emoji to be removed.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.
        """
        return await self._client.remove_reaction_from_message(
            self.id, self.group_id, emoji
        )

    def __repr__(self) -> str:
        return f'<GroupMessage id="{self.id}">'