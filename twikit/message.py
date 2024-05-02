from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx import Response

    from twikit.client import Client


class Message:
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
    attachment : :class:`dict`
        Attachment Information.
    """

    def __init__(self, client: Client, data: dict, sender_id: str, recipient_id: str) -> None:
        self._client = client
        self.sender_id = sender_id
        self.recipient_id = recipient_id

        self.id: str = data['id']
        self.time: str = data['time']
        self.text: str = data['text']
        self.attachment: dict | None = data.get('attachment')

    def reply(self, text: str, media_id: str | None = None) -> Message:
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
            `Message` object containing information about the message sent.

        See Also
        --------
        Client.send_dm
        """
        user_id = self._client.user_id()
        send_to = self.recipient_id if user_id == self.sender_id else self.sender_id
        return self._client.send_dm(send_to, text, media_id, self.id)

    def add_reaction(self, emoji: str) -> Response:
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
        conversation_id = self._get_conversation_id()
        return self._client.add_reaction_to_message(self.id, conversation_id, emoji)

    def remove_reaction(self, emoji: str) -> Response:
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
        conversation_id = self._get_conversation_id()
        return self._client.remove_reaction_from_message(self.id, conversation_id, emoji)

    def _get_conversation_id(self) -> str:
        """
        Returns a unique conversation ID based on the user IDs involved.

        Args:
            self: The instance of the class.

        Returns:
            str: A string representing the unique conversation ID.
        """
        user_id = self._client.user_id()
        partner_id = self.recipient_id if user_id == self.sender_id else self.sender_id
        return f'{partner_id}-{user_id}'

    def delete(self) -> Response:
        """
        Deletes the message.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        See Also
        --------
        Client.delete_dm
        """
        return self._client.delete_dm(self.id)

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, Message) and self.id == __value.id

    def __ne__(self, __value: object) -> bool:
        return not self == __value

    def __repr__(self) -> str:
        return f'<Message id="{self.id}">'
