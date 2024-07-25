from __future__ import annotations

from typing import TYPE_CHECKING

from ..utils import find_dict
from .user import User

if TYPE_CHECKING:
    from .client import GuestClient


class Tweet:
    """
    Attributes
    ----------
    id : :class:`str`
        The unique identifier of the tweet.
    created_at : :class:`str`
        The date and time when the tweet was created.
    created_at_datetime : :class:`datetime`
        The created_at converted to datetime.
    user: :class:`.guest.user.User`
        Author of the tweet.
    text : :class:`str`
        The full text of the tweet.
    lang : :class:`str`
        The language of the tweet.
    in_reply_to : :class:`str`
        The tweet ID this tweet is in reply to, if any
    is_quote_status : :class:`bool`
        Indicates if the tweet is a quote status.
    quote : :class:`.guest.tweet.Tweet` | None
        The Tweet being quoted (if any)
    retweeted_tweet : :class:`.guest.tweet.Tweet` | None
        The Tweet being retweeted (if any)
    possibly_sensitive : :class:`bool`
        Indicates if the tweet content may be sensitive.
    possibly_sensitive_editable : :class:`bool`
        Indicates if the tweet's sensitivity can be edited.
    quote_count : :class:`int`
        The count of quotes for the tweet.
    media : :class:`list`
        A list of media entities associated with the tweet.
    reply_count : :class:`int`
        The count of replies to the tweet.
    favorite_count : :class:`int`
        The count of favorites or likes for the tweet.
    favorited : :class:`bool`
        Indicates if the tweet is favorited.
    view_count: :class:`int` | None
        The count of views.
    view_count_state : :class:`str` | None
        The state of the tweet views.
    retweet_count : :class:`int`
        The count of retweets for the tweet.
    place : :class:`.Place` | None
        The location associated with the tweet.
    editable_until_msecs : :class:`int`
        The timestamp until which the tweet is editable.
    is_translatable : :class:`bool`
        Indicates if the tweet is translatable.
    is_edit_eligible : :class:`bool`
        Indicates if the tweet is eligible for editing.
    edits_remaining : :class:`int`
        The remaining number of edits allowed for the tweet.
    reply_to: list[:class:`Tweet`] | None
        A list of Tweet objects representing the tweets to which to reply.
    related_tweets : list[:class:`Tweet`] | None
        Related tweets.
    hashtags: list[:class:`str`]
        Hashtags included in the tweet text.
    has_card : :class:`bool`
        Indicates if the tweet contains a card.
    thumbnail_title : :class:`str` | None
        The title of the webpage displayed inside tweet's card.
    thumbnail_url : :class:`str` | None
        Link to the image displayed in the tweet's card.
    urls : :class:`list`
        Information about URLs contained in the tweet.
    full_text : :class:`str` | None
        The full text of the tweet.
    """

    def __init__(self, client: GuestClient, data: dict, user: User = None) -> None:
        self._client = client
        self._data = data
        self.user = user

        self.reply_to: list[Tweet] | None = None
        self.related_tweets: list[Tweet] | None = None
        self.thread: list[Tweet] | None = None

        self.id: str = data['rest_id']
        legacy = data['legacy']
        self.created_at: str = legacy['created_at']
        self.text: str = legacy['full_text']
        self.lang: str = legacy['lang']
        self.is_quote_status: bool = legacy['is_quote_status']
        self.in_reply_to: str | None = self._data['legacy'].get('in_reply_to_status_id_str')
        self.is_quote_status: bool = legacy['is_quote_status']
        self.possibly_sensitive: bool = legacy.get('possibly_sensitive')
        self.possibly_sensitive_editable: bool = legacy.get('possibly_sensitive_editable')
        self.quote_count: int = legacy['quote_count']
        self.media: list = legacy['entities'].get('media')
        self.reply_count: int = legacy['reply_count']
        self.favorite_count: int = legacy['favorite_count']
        self.favorited: bool = legacy['favorited']
        self.retweet_count: int = legacy['retweet_count']
        self._place_data = legacy.get('place')
        self.editable_until_msecs: int = data['edit_control'].get('editable_until_msecs')
        self.is_translatable: bool = data.get('is_translatable')
        self.is_edit_eligible: bool = data['edit_control'].get('is_edit_eligible')
        self.edits_remaining: int = data['edit_control'].get('edits_remaining')
        self.view_count: str = data['views'].get('count') if 'views' in data else None
        self.view_count_state: str = data['views'].get('state') if 'views' in data else None
        self.has_community_notes: bool = data.get('has_birdwatch_notes')

        if data.get('quoted_status_result'):
            quoted_tweet = data.pop('quoted_status_result')['result']
            if 'tweet' in quoted_tweet:
                quoted_tweet = quoted_tweet['tweet']
            if quoted_tweet.get('__typename') != 'TweetTombstone':
                quoted_user = User(client, quoted_tweet['core']['user_results']['result'])
                self.quote: Tweet = Tweet(client, quoted_tweet, quoted_user)
        else:
            self.quote = None

        if legacy.get('retweeted_status_result'):
            retweeted_tweet = legacy.pop('retweeted_status_result')['result']
            if 'tweet' in retweeted_tweet:
                retweeted_tweet = retweeted_tweet['tweet']
            retweeted_user = User(
                client, retweeted_tweet['core']['user_results']['result']
            )
            self.retweeted_tweet: Tweet = Tweet(
                client, retweeted_tweet, retweeted_user
            )
        else:
            self.retweeted_tweet = None

        note_tweet_results = find_dict(data, 'note_tweet_results', find_one=True)
        self.full_text: str = self.text
        if note_tweet_results:
            text_list = find_dict(note_tweet_results, 'text', find_one=True)
            if text_list:
                self.full_text = text_list[0]

            entity_set = note_tweet_results[0]['result']['entity_set']
            self.urls: list = entity_set.get('urls')
            hashtags = entity_set.get('hashtags', [])
        else:
            self.urls: list = legacy['entities'].get('urls')
            hashtags = legacy['entities'].get('hashtags', [])

        self.hashtags: list[str] = [
            i['text'] for i in hashtags
        ]

        self.community_note = None
        if 'birdwatch_pivot' in data:
            community_note_data = data['birdwatch_pivot']
            if 'note' in community_note_data:
                self.community_note = {
                    'id': community_note_data['note']['rest_id'],
                    'text': community_note_data['subtitle']['text']
                }

        if (
            'card' in data and
            'legacy' in data['card'] and
            'name' in data['card']['legacy'] and
            data['card']['legacy']['name'].startswith('poll')
        ):
            self._poll_data = data['card']
        else:
            self._poll_data = None

        self.thumbnail_url = None
        self.thumbnail_title = None
        self.has_card = 'card' in data
        if (
            'card' in data and
            'legacy' in data['card'] and
            'binding_values' in data['card']['legacy']
        ):
            card_data = data['card']['legacy']['binding_values']

            if isinstance(card_data, list):
                binding_values = {
                    i.get('key'): i.get('value')
                    for i in card_data
                }

            if 'title' in binding_values and 'string_value' in binding_values['title']:
                self.thumbnail_title = binding_values['title']['string_value']

            if (
                'thumbnail_image_original' in binding_values and
                'image_value' in binding_values['thumbnail_image_original'] and
                'url' in binding_values['thumbnail_image_original']['image_value']
            ):
                self.thumbnail_url = binding_values['thumbnail_image_original']['image_value']['url']

    async def update(self) -> None:
        new = await self._client.get_tweet_by_id(self.id)
        self.__dict__.update(new.__dict__)

    def __repr__(self) -> str:
        return f'<Tweet id="{self.id}">'

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, Tweet) and self.id == __value.id

    def __ne__(self, __value: object) -> bool:
        return not self == __value