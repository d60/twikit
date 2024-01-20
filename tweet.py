from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import Client
    from user import User


class Tweet:
    """
    Attributes
    ----------
    id (str): The unique identifier of the tweet.
    text (str): The full text of the tweet.
    lang (str): The language of the tweet.
    is_quote_status (bool): Indicates if the tweet is a quote status.
    possibly_sensitive (bool): Indicates if the tweet content may be sensitive.
    possibly_sensitive_editable (bool): Indicates if the tweet's sensitivity can be edited.
    quote_count (int): The count of quotes for the tweet.
    media (list): A list of media entities associated with the tweet.
    reply_count (int): The count of replies to the tweet.
    favorite_count (int): The count of favorites or likes for the tweet.
    favorited (bool): Indicates if the tweet is favorited.
    retweet_count (int): The count of retweets for the tweet.
    editable_until_msecs (int): The timestamp until which the tweet is editable.
    is_translatable (bool): Indicates if the tweet is translatable.
    is_edit_eligible (bool): Indicates if the tweet is eligible for editing.
    edits_remaining (int): The remaining number of edits allowed for the tweet.
    state (str): The state of the tweet views.
    """

    def __init__(self, client: Client, data: dict, user: User) -> None:
        self._client = client
        self.user = user

        self.id = data["legacy"]["id_str"]
        self.text = data["legacy"]["full_text"]
        self.lang = data["legacy"]["lang"]
        self.is_quote_status = data["legacy"]["is_quote_status"]
        self.possibly_sensitive = data["legacy"].get("possibly_sensitive")
        self.possibly_sensitive_editable = data["legacy"].get("possibly_sensitive_editable")
        self.quote_count = data["legacy"]["quote_count"]
        self.media = data["legacy"]["entities"].get("media")
        self.reply_count = data["legacy"]["reply_count"]
        self.favorite_count = data["legacy"]["favorite_count"]
        self.favorited = data["legacy"]["favorited"]
        self.retweet_count = data["legacy"]["retweet_count"]
        self.editable_until_msecs = data["edit_control"]["editable_until_msecs"]
        self.is_translatable = data["is_translatable"]
        self.is_edit_eligible = data["edit_control"]["is_edit_eligible"]
        self.edits_remaining = data["edit_control"]["edits_remaining"]
        self.state = data["views"]["state"]

    def __repr__(self) -> str:
        return f'<Tweet id="{self.id}">'
