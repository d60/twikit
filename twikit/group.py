from __future__ import annotations

from typing import TYPE_CHECKING

from .message import Message

if TYPE_CHECKING:
    from httpx import Response

    from .client import Client
    from .utils import Result


class Group:
    """
    Represents a group.

    Attributes
    ----------
    id : str
        The ID of the group.
    name : str | None
        The name of the group.
    members : list[str]
        Member IDs
    """
    def __init__(self, client: Client, group_id: str, data: dict) -> None:
        self._client = client
        self.id = group_id

        entries = data['conversation_timeline']['entries']
        name_update_log = next(
            filter(lambda x: 'conversation_name_update' in x, entries),
            None
        )
        self.name: str | None = (
            name_update_log['conversation_name_update']['conversation_name']
            if name_update_log else None
        )

        members = data['conversation_timeline']['users'].values()
        self.members: list[str] = [i['id_str'] for i in members]

    def get_history(self, max_id: str | None = None) -> Result[GroupMessage]:
        """
        Retrieves the DM conversation history in the group.

        Parameters
        ----------
        max_id : str, default=None
            If specified, retrieves messages older than the specified max_id.

        Returns
        -------
        Result[GroupMessage]
            A Result object containing a list of GroupMessage objects
            representing the DM conversation history.

        Examples
        --------
        >>> messages = group.get_history()
        >>> for message in messages:
        >>>     print(message)
        <GroupMessage id="...">
        <GroupMessage id="...">
        ...
        ...

        >>> more_messages = messages.next()  # Retrieve more messages
        >>> for message in more_messages:
        >>>     print(message)
        <GroupMessage id="...">
        <GroupMessage id="...">
        ...
        ...
        """
        return self._client.get_group_dm_history(self.id, max_id)

    def add_members(self, user_ids: list[str]) -> Response:
        """Adds members to the group.

        Parameters
        ----------
        user_ids : list[str]
            List of IDs of users to be added.

        Returns
        -------
        httpx.Response
            Response returned from twitter api.

        Examples
        --------
        >>> members = ['...']
        >>> group.add_members(members)
        """
        return self._client.add_members_to_group(self.id, user_ids)

    def change_name(self, name: str) -> Response:
        """Changes group name

        Parameters
        ----------
        name : str
            New name.

        Returns
        -------
        httpx.Response
            Response returned from twitter api.
        """
        return self._client.change_group_name(self.id, name)

    def send_message(
        self,
        text: str,
        media_id: str | None = None,
        reply_to: str | None = None
    ) -> GroupMessage:
        """
        Sends a message to the group.

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
        GroupMessage
            `Message` object containing information about the message sent.

        Examples
        --------
        >>> # send DM with media
        >>> group_id = '000000000'
        >>> media_id = client.upload_media('image.png', 0)
        >>> message = group.send_message('text', media_id)
        >>> print(message)
        <GroupMessage id='...'>
        """
        return self._client.send_dm_to_group(self.id, text, media_id, reply_to)

    def __repr__(self) -> str:
        return f'<Group id="{self.id}">'


class GroupMessage(Message):
    """
    Represents a direct message.

    Attributes
    ----------
    id : str
        The ID of the message.
    time : str
        The timestamp of the message.
    text : str
        The text content of the message.
    attachment : str
        The media URL associated with any attachment in the message.
    group_id : str
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

    def group(self) -> Group:
        """
        Gets the group to which the message was sent.
        """
        return self._client.get_group(self.group_id)

    def reply(self, text: str, media_id: str | None = None) -> GroupMessage:
        """Replies to the message.

        Parameters
        ----------
        text : str
            The text content of the direct message.
        media_id : str, default=None
            The media ID associated with any media content
            to be included in the message.
            Media ID can be received by using the :func:`.upload_media` method.

        Returns
        -------
        Message
            `GroupMessage` object containing information about
            the message sent.

        See Also
        --------
        Client.send_dm_to_group
        """
        return self._client.send_dm_to_group(
            self.group_id, text, media_id, self.id
        )

    def add_reaction(self, emoji: str) -> Response:
        """
        Adds a reaction to the message.

        Parameters
        ----------
        emoji : str
            The emoji to be added as a reaction.

        Returns
        -------
        httpx.Response
            Response returned from twitter api.
        """
        return self._client.add_reaction_to_message(
            self.id, self.group_id, emoji
        )

    def remove_reaction(self, emoji: str) -> Response:
        """
        Removes a reaction from the message.

        Parameters
        ----------
        emoji : str
            The emoji to be removed.

        Returns
        -------
        httpx.Response
            Response returned from twitter api.
        """
        return self._client.remove_reaction_from_message(
            self.id, self.group_id, emoji
        )

    def __repr__(self) -> str:
        return f'<GroupMessage id="{self.id}">'
