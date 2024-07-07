from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx import Response

    from .client.client import Client
    from .tweet import Tweet
    from .utils import Result


class BookmarkFolder:
    """
    Attributes
    ----------
    id : :class:`str`
        The ID of the folder.
    name : :class:`str`
        The name of the folder
    media : :class:`str`
        Icon image data.
    """
    def __init__(self, client: Client, data: dict) -> None:
        self._client = client

        self.id: str = data['id']
        self.name: str = data['name']
        self.media: dict = data['media']

    async def get_tweets(self, cursor: str | None = None) -> Result[Tweet]:
        """
        Retrieves tweets from the folder.
        """
        return await self._client.get_bookmarks(
            cursor=cursor, folder_id=self.id
        )

    async def edit(self, name: str) -> BookmarkFolder:
        """
        Edits the folder.
        """
        return await self._client.edit_bookmark_folder(self.id, name)

    async def delete(self) -> Response:
        """
        Deletes the folder.
        """
        return await self._client.delete_bookmark_folder(self.id)

    async def add(self, tweet_id: str) -> Response:
        """
        Adds a tweet to the folder.
        """
        return await self._client.bookmark_tweet(tweet_id, self.id)

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, BookmarkFolder) and self.id == __value.id

    def __ne__(self, __value: object) -> bool:
        return not self == __value

    def __repr__(self) -> str:
        return f'<BookmarkFolder id="{self.id}">'
