from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx import Response

    from .client import Client


class Message:
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
    """
    def __init__(
        self,
        client: Client,
        data: dict,
        sender_id: str,
        recipient_id: str
    ) -> None:
        self._client = client
        self.sender_id = sender_id
        self.recipient_id = recipient_id

        self.id: str = data['id']
        self.time: str = data['time']
        self.text: str = data['text']
        if 'attachment' in data:
            attachment = list(data['attachment'].values())[0]
            self.attachment: str | None = attachment['media_url_https']
        else:
            self.attachment = None

    async def reply(self, text: str, media_id: str | None = None) -> Message:
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
            `Message` object containing information about the message sent.

        See Also
        --------
        Client.send_dm
        """
        user_id = await self._client.user_id()
        send_to = (
            self.recipient_id
            if user_id == self.sender_id else
            self.sender_id
        )
        return await self._client.send_dm(send_to, text, media_id, self.id)

    async def delete(self) -> Response:
        """
        Deletes the message.

        Returns
        -------
        httpx.Response
            Response returned from twitter api.

        See Also
        --------
        Client.delete_dm
        """
        return await self._client.delete_dm(self.id)

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, Message) and self.id == __value.id

    def __ne__(self, __value: object) -> bool:
        return not self == __value

    def __repr__(self) -> str:
        return f'<Message id="{self.id}">'
