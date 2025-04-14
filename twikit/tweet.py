from __future__ import annotations

import re
from datetime import datetime
from typing import TYPE_CHECKING

from .geo import Place
from .media import MEDIA_TYPE, _media_from_data
from .user import User
from .utils import find_dict, timestamp_to_datetime

if TYPE_CHECKING:
    from httpx import Response

    from .client.client import Client
    from .utils import Result


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
    user: :class:`User`
        Author of the tweet.
    text : :class:`str`
        The full text of the tweet.
    lang : :class:`str`
        The language of the tweet.
    in_reply_to : :class:`str`
        The tweet ID this tweet is in reply to, if any
    is_quote_status : :class:`bool`
        Indicates if the tweet is a quote status.
    quote : :class:`Tweet` | None
        The Tweet being quoted (if any)
    retweeted_tweet : :class:`Tweet` | None
        The Tweet being retweeted (if any)
    possibly_sensitive : :class:`bool`
        Indicates if the tweet content may be sensitive.
    possibly_sensitive_editable : :class:`bool`
        Indicates if the tweet's sensitivity can be edited.
    quote_count : :class:`int`
        The count of quotes for the tweet.
    media : list[:class:`.media.Photo` | :class:`.media.AnimatedGif` | :class:`.media.Video`]
        A list of media entities associated with the tweet.
        https://github.com/d60/twikit/blob/main/examples/download_tweet_media.py
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
    bookmark_count : :class:`int`
        The count of bookmarks for the tweet.
    bookmarked : :class:`bool`
        Indicates if the tweet is bookmarked.
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
    edit_tweet_ids : :class:`list`[:class:`int`]
        List of tweet IDs representing the edit history of the tweet.
    replies: Result[:class:`Tweet`] | None
        Replies to the tweet.
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

    def __init__(self, client: Client, data: dict, user: User = None) -> None:
        self._client = client
        self._data = data
        self._legacy: dict = self._data['legacy']
        self.user = user

        self.replies: Result[Tweet] | None = None
        self.reply_to: list[Tweet] | None = None
        self.related_tweets: list[Tweet] | None = None
        self.thread: list[Tweet] | None = None

    @property
    def id(self) -> str:
        return self._data['rest_id']

    @property
    def created_at(self) -> str:
        return self._legacy['created_at']

    @property
    def text(self) -> str:
        return self._legacy['full_text']

    @property
    def lang(self) -> str:
        return self._legacy['lang']

    @property
    def in_reply_to(self) -> str | None:
        return self._legacy.get('in_reply_to_status_id_str')

    @property
    def is_quote_status(self) -> bool:
        return self._legacy['is_quote_status']

    @property
    def possibly_sensitive(self) -> bool:
        return self._legacy.get('possibly_sensitive')

    @property
    def possibly_sensitive_editable(self) -> bool:
        return self._legacy.get('possibly_sensitive_editable')

    @property
    def quote_count(self) -> int:
        return self._legacy.get('quote_count')

    @property
    def reply_count(self) -> int:
        return self._legacy['reply_count']

    @property
    def favorite_count(self) -> int:
        return self._legacy['favorite_count']

    @property
    def favorited(self) -> bool:
        return self._legacy['favorited']

    @property
    def retweet_count(self) -> int:
        return self._legacy['retweet_count']

    @property
    def _place_data(self):
        return self._legacy.get('place')

    @property
    def bookmark_count(self) -> int:
        return self._legacy.get('bookmark_count')

    @property
    def bookmarked(self) -> bool:
        return self._legacy.get('bookmarked')

    @property
    def edit_tweet_ids(self) -> list[int]:
        return self._data['edit_control'].get('edit_tweet_ids', [])

    @property
    def editable_until_msecs(self) -> int:
        return self._data['edit_control'].get('editable_until_msecs')

    @property
    def is_translatable(self) -> bool:
        return self._data.get('is_translatable')

    @property
    def is_edit_eligible(self) -> bool:
        return self._data['edit_control'].get('is_edit_eligible')

    @property
    def edits_remaining(self) -> int:
        return self._data['edit_control'].get('edits_remaining')

    @property
    def view_count(self) -> int | None:
        return self._data.get('views', {}).get('count')

    @property
    def view_count_state(self) -> str | None:
        return self._data.get('views', {}).get('state')

    @property
    def has_community_notes(self) -> bool:
        return self._data.get('has_birdwatch_notes')

    @property
    def quote(self) -> Tweet | None:
        if self._data.get('quoted_status_result'):
            quoted_tweet = self._data['quoted_status_result']
            return tweet_from_data(self._client, quoted_tweet)

    @property
    def retweeted_tweet(self) -> Tweet | None:
        if self._legacy.get('retweeted_status_result'):
            retweeted_tweet = self._legacy['retweeted_status_result']
            return tweet_from_data(self._client, retweeted_tweet)

    @property
    def _note_tweet_results(self) -> dict | None:
        if 'note_tweet' in self._data and 'note_tweet_results' in self._data['note_tweet']:
            return self._data['note_tweet']['note_tweet_results']

    @property
    def full_text(self) -> str:
        note_tweet_results = self._note_tweet_results
        if note_tweet_results:
            return note_tweet_results['result']['text']
        return self.text

    @property
    def hashtags(self) -> list[str]:
        note_tweet_results = self._note_tweet_results
        if note_tweet_results:
            entity_set = note_tweet_results['result']['entity_set']
            hashtags = entity_set.get('hashtags', [])
        else:
            hashtags = self._legacy['entities'].get('hashtags', [])
        return [i['text'] for i in hashtags]

    @property
    def urls(self) -> list[str]:
        note_tweet_results = self._note_tweet_results
        if note_tweet_results:
            entity_set = note_tweet_results['result']['entity_set']
            return entity_set.get('urls')
        return self._legacy['entities'].get('urls')

    @property
    def community_note(self) -> dict | None:
        community_note_data = self._data.get('birdwatch_pivot')
        if community_note_data and 'note' in community_note_data:
            return {
                'id': community_note_data['note']['rest_id'],
                'text': community_note_data['subtitle']['text']
            }

    @property
    def _binding_values(self) -> dict | None:
        if (
            'card' in self._data and
            'legacy' in self._data['card'] and
            'binding_values' in self._data['card']['legacy']
        ):
            card_data = self._data['card']['legacy']['binding_values']
            if isinstance(card_data, list):
                return {
                    i.get('key'): i.get('value')
                    for i in card_data
                }

    @property
    def has_card(self) -> bool:
        return 'card' in self._data

    @property
    def thumbnail_title(self) -> str | None:
        binding_values = self._binding_values
        if (
            binding_values and
            'title' in binding_values and
            'string_value' in binding_values['title']
        ):
            return binding_values['title']['string_value']

    @property
    def thumbnail_url(self) -> str | None:
        binding_values = self._binding_values
        if (
            binding_values and
            'thumbnail_image_original' in binding_values and
            'image_value' in binding_values['thumbnail_image_original'] and
            'url' in binding_values['thumbnail_image_original']['image_value']
        ):
            return binding_values['thumbnail_image_original']['image_value']['url']

    @property
    def created_at_datetime(self) -> datetime:
        return timestamp_to_datetime(self.created_at)

    @property
    def poll(self) -> Poll:
        if (
            'card' in self._data and
            'legacy' in self._data['card'] and
            'name' in self._data['card']['legacy'] and
            self._data['card']['legacy']['name'].startswith('poll')
        ):
            return Poll(self._client, self._data['card'], self)

    @property
    def place(self) -> Place:
        if self._place_data:
            return Place(self._client, self._place_data)

    @property
    def media(self) -> list[MEDIA_TYPE]:
        media_data = self._legacy['entities'].get('media', [])
        m = []
        for entry in media_data:
            media_obj = _media_from_data(self._client, entry)
            if not media_obj:
                continue
            m.append(media_obj)
        return m

    async def delete(self) -> Response:
        """Deletes the tweet.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> await tweet.delete()
        """
        return await self._client.delete_tweet(self.id)

    async def favorite(self) -> Response:
        """
        Favorites the tweet.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        See Also
        --------
        Client.favorite_tweet
        """
        return await self._client.favorite_tweet(self.id)

    async def unfavorite(self) -> Response:
        """
        Favorites the tweet.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        See Also
        --------
        Client.unfavorite_tweet
        """
        return await self._client.unfavorite_tweet(self.id)

    async def retweet(self) -> Response:
        """
        Retweets the tweet.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        See Also
        --------
        Client.retweet
        """
        return await self._client.retweet(self.id)

    async def delete_retweet(self) -> Response:
        """
        Deletes the retweet.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        See Also
        --------
        Client.delete_retweet
        """
        return await self._client.delete_retweet(self.id)

    async def bookmark(self) -> Response:
        """
        Adds the tweet to bookmarks.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        See Also
        --------
        Client.bookmark_tweet
        """
        return await self._client.bookmark_tweet(self.id)

    async def delete_bookmark(self) -> Response:
        """
        Removes the tweet from bookmarks.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        See Also
        --------
        Client.delete_bookmark
        """
        return await self._client.delete_bookmark(self.id)

    async def reply(
        self,
        text: str = '',
        media_ids: list[str] | None = None,
        **kwargs
    ) -> Tweet:
        """
        Replies to the tweet.

        Parameters
        ----------
        text : :class:`str`, default=''
            The text content of the reply.
        media_ids : list[:class:`str`], default=None
            A list of media IDs or URIs to attach to the reply.
            Media IDs can be obtained by using the `upload_media` method.

        Returns
        -------
        :class:`Tweet`
            The created tweet.

        Examples
        --------
        >>> tweet_text = 'Example text'
        >>> media_ids = [
        ...     client.upload_media('image1.png'),
        ...     client.upload_media('image2.png')
        ... ]
        >>> await tweet.reply(
        ...     tweet_text,
        ...     media_ids=media_ids
        ... )

        See Also
        --------
        `Client.upload_media`
        """
        return await self._client.create_tweet(
            text, media_ids, reply_to=self.id, **kwargs
        )

    async def get_retweeters(
        self, count: str = 40, cursor: str | None = None
    ) -> Result[User]:
        """
        Retrieve users who retweeted the tweet.

        Parameters
        ----------
        count : :class:`int`, default=40
            The maximum number of users to retrieve.
        cursor : :class:`str`, default=None
            A string indicating the position of the cursor for pagination.

        Returns
        -------
        Result[:class:`User`]
            A list of users who retweeted the tweet.

        Examples
        --------
        >>> tweet_id = '...'
        >>> retweeters = tweet.get_retweeters()
        >>> print(retweeters)
        [<User id="...">, <User id="...">, ..., <User id="...">]

        >>> more_retweeters = retweeters.next()  # Retrieve more retweeters.
        >>> print(more_retweeters)
        [<User id="...">, <User id="...">, ..., <User id="...">]
        """
        return await self._client.get_retweeters(self.id, count, cursor)

    async def get_favoriters(
        self, count: str = 40, cursor: str | None = None
    ) -> Result[User]:
        """
        Retrieve users who favorited a specific tweet.

        Parameters
        ----------
        tweet_id : :class:`str`
            The ID of the tweet.
        count : :class:`int`, default=40
            The maximum number of users to retrieve.
        cursor : :class:`str`, default=None
            A string indicating the position of the cursor for pagination.

        Returns
        -------
        Result[:class:`User`]
            A list of users who favorited the tweet.

        Examples
        --------
        >>> tweet_id = '...'
        >>> favoriters = tweet.get_favoriters()
        >>> print(favoriters)
        [<User id="...">, <User id="...">, ..., <User id="...">]

        >>> more_favoriters = favoriters.next()  # Retrieve more favoriters.
        >>> print(more_favoriters)
        [<User id="...">, <User id="...">, ..., <User id="...">]
        """
        return await self._client.get_favoriters(self.id, count, cursor)

    async def get_similar_tweets(self) -> list[Tweet]:
        """
        Retrieves tweets similar to the tweet (Twitter premium only).

        Returns
        -------
        list[:class:`Tweet`]
            A list of Tweet objects representing tweets
            similar to the tweet.
        """
        return await self._client.get_similar_tweets(self.id)

    async def update(self) -> None:
        new = await self._client.get_tweet_by_id(self.id)
        self.__dict__.update(new.__dict__)

    def __repr__(self) -> str:
        return f'<Tweet id="{self.id}">'

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, Tweet) and self.id == __value.id

    def __ne__(self, __value: object) -> bool:
        return not self == __value


def tweet_from_data(client: Client, data: dict) -> Tweet:
    ':meta private:'
    tweet_data_ = find_dict(data, 'result', True)
    if not tweet_data_:
        return None
    tweet_data = tweet_data_[0]

    if tweet_data.get('__typename') == 'TweetTombstone':
        return None
    if 'tweet' in tweet_data:
        tweet_data = tweet_data['tweet']
    if 'core' not in tweet_data:
        return None
    if 'result' not in tweet_data['core']['user_results']:
        return None
    if 'legacy' not in tweet_data:
        return None

    user_data = tweet_data['core']['user_results']['result']
    return Tweet(client, tweet_data, User(client, user_data))


class ScheduledTweet:
    def __init__(self, client: Client, data: dict) -> None:
        self._client = client

        self.id = data['rest_id']
        self.execute_at: int = data['scheduling_info']['execute_at']
        self.state: str = data['scheduling_info']['state']
        self.type: str = data['tweet_create_request']['type']
        self.text: str = data['tweet_create_request']['status']
        self.media = [i['media_info'] for i in data.get('media_entities', [])]

    async def delete(self) -> Response:
        """
        Delete the scheduled tweet.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.
        """
        return await self._client.delete_scheduled_tweet(self.id)

    def __repr__(self) -> str:
        return f'<ScheduledTweet id="{self.id}">'


class TweetTombstone:
    def __init__(self, client: Client, tweet_id: str, data: dict) -> None:
        self._client = client
        self.id = tweet_id
        self.text: str = data['text']['text']

    def __repr__(self) -> str:
        return f'<TweetTombstone id="{self.id}">'

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, TweetTombstone) and self.id == __value.id

    def __ne__(self, __value: object) -> bool:
        return not self == __value


class Poll:
    """Represents a poll associated with a tweet.
    Attributes
    ----------
    tweet : :class:`Tweet`
        The tweet associated with the poll.
    id : :class:`str`
        The unique identifier of the poll.
    name : :class:`str`
        The name of the poll.
    choices : list[:class:`dict`]
        A list containing dictionaries representing poll choices.
        Each dictionary contains 'label' and 'count' keys
        for choice label and count.
    duration_minutes : :class:`int`
        The duration of the poll in minutes.
    end_datetime_utc : :class:`str`
        The end date and time of the poll in UTC format.
    last_updated_datetime_utc : :class:`str`
        The last updated date and time of the poll in UTC format.
    selected_choice : :class:`str` | None
        Number of the selected choice.
    """

    def __init__(
        self, client: Client, data: dict, tweet: Tweet | None = None
    ) -> None:
        self._client = client
        self.tweet = tweet

        legacy = data['legacy']
        binding_values = legacy['binding_values']

        if isinstance(legacy['binding_values'], list):
            binding_values = {
                i.get('key'): i.get('value')
                for i in legacy['binding_values']
            }

        self.id: str = data['rest_id']
        self.name: str = legacy['name']

        choices_number = int(re.findall(
            r'poll(\d)choice_text_only', self.name
        )[0])
        choices = []

        for i in range(1, choices_number + 1):
            choice_label = binding_values[f'choice{i}_label']
            choice_count = binding_values.get(f'choice{i}_count', {})
            choices.append({
                'number': str(i),
                'label': choice_label['string_value'],
                'count': choice_count.get('string_value', '0')
            })

        self.choices = choices

        self.duration_minutes = int(binding_values['duration_minutes']['string_value'])
        self.end_datetime_utc: str = binding_values['end_datetime_utc']['string_value']
        updated = binding_values['last_updated_datetime_utc']['string_value']
        self.last_updated_datetime_utc: str = updated

        self.counts_are_final: bool = binding_values['counts_are_final']['boolean_value']

        if 'selected_choice' in binding_values:
            self.selected_choice: str = binding_values['selected_choice']['string_value']
        else:
            self.selected_choice = None

    async def vote(self, selected_choice: str) -> Poll:
        """
        Vote on the poll with the specified selected choice.
        Parameters
        ----------
        selected_choice : :class:`str`
            The label of the selected choice for the vote.
        Returns
        -------
        :class:`Poll`
            The Poll object representing the updated poll after voting.
        """
        return await self._client.vote(
            selected_choice,
            self.id,
            self.tweet.id,
            self.name
        )

    def __repr__(self) -> str:
        return f'<Poll id="{self.id}">'

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, Poll) and self.id == __value.id

    def __ne__(self, __value: object) -> bool:
        return not self == __value


class CommunityNote:
    """Represents a community note.

    Attributes
    ----------
    id : :class:`str`
        The ID of the community note.
    text : :class:`str`
        The text content of the community note.
    misleading_tags : list[:class:`str`]
        A list of tags indicating misleading information.
    trustworthy_sources : :class:`bool`
        Indicates if the sources are trustworthy.
    helpful_tags : list[:class:`str`]
        A list of tags indicating helpful information.
    created_at : :class:`int`
        The timestamp when the note was created.
    can_appeal : :class:`bool`
        Indicates if the note can be appealed.
    appeal_status : :class:`str`
        The status of the appeal.
    is_media_note : :class:`bool`
        Indicates if the note is related to media content.
    media_note_matches : :class:`str`
        Matches related to media content.
    birdwatch_profile : :class:`dict`
        Birdwatch profile associated with the note.
    tweet_id : :class:`str`
        The ID of the tweet associated with the note.
    """
    def __init__(self, client: Client, data: dict) -> None:
        self._client = client
        self.id: str = data['rest_id']

        data_v1 = data['data_v1']
        self.text: str = data_v1['summary']['text']
        self.misleading_tags: list[str] = data_v1.get('misleading_tags')
        self.trustworthy_sources: bool = data_v1.get('trustworthy_sources')
        self.helpful_tags: list[str] = data.get('helpful_tags')
        self.created_at: int = data.get('created_at')
        self.can_appeal: bool = data.get('can_appeal')
        self.appeal_status: str = data.get('appeal_status')
        self.is_media_note: bool = data.get('is_media_note')
        self.media_note_matches: str = data.get('media_note_matches')
        self.birdwatch_profile: dict = data.get('birdwatch_profile')
        self.tweet_id: str = data['tweet_results']['result']['rest_id']

    async def update(self) -> None:
        new = await self._client.get_community_note(self.id)
        self.__dict__.update(new.__dict__)

    def __repr__(self) -> str:
        return f'<CommunityNote id="{self.id}">'

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, CommunityNote) and self.id == __value.id

    def __ne__(self, __value: object) -> bool:
        return not self == __value
