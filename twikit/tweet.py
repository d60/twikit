from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from .user import User
from .utils import find_dict, timestamp_to_datetime

if TYPE_CHECKING:
    from httpx import Response

    from .client import Client
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
    quote : :class:`Tweet`
        The Tweet being quoted (if any)
    retweeted : :class:`bool`
        Whether the tweet is a retweet
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
    view_count: :class:`int`
        The count of views.
    retweet_count : :class:`int`
        The count of retweets for the tweet.
    editable_until_msecs : :class:`int`
        The timestamp until which the tweet is editable.
    is_translatable : :class:`bool`
        Indicates if the tweet is translatable.
    is_edit_eligible : :class:`bool`
        Indicates if the tweet is eligible for editing.
    edits_remaining : :class:`int`
        The remaining number of edits allowed for the tweet.
    state : :class:`str`
        The state of the tweet views.
    replies: Result[:class:`Tweet`] | None
        Replies to the tweet.
    reply_to: list[:class:`Tweet`] | None
        A list of Tweet objects representing the tweets to which to reply.
    related_tweets : list[:class:`Tweet`] | None
        Related tweets.
    hashtags: list[:class:`str`]
        Hashtags included in the tweet text.
    poll : :class:`Poll`
        Poll attached to the tweet.
    """

    def __init__(self, client: Client, data: dict, user: User = None) -> None:
        self._client = client
        self._data = data
        self.user = user

        self.replies: Result[Tweet] | None = None
        self.reply_to: list[Tweet] | None = None
        self.related_tweets: list[Tweet] | None = None

        self.id: str = data['rest_id']

        legacy = data['legacy']
        self.created_at: str = legacy['created_at']
        self.text: str = legacy['full_text']

        self.lang: str = legacy['lang']
        self.is_quote_status: bool = legacy['is_quote_status']
        self.in_reply_to: str | None = self._data['legacy'].get(
            'in_reply_to_status_id_str'
        )

        if data.get('quoted_status_result'):
            quoted_tweet = data.pop('quoted_status_result')['result']
            if 'tweet' in quoted_tweet:
                quoted_tweet = quoted_tweet['tweet']
            if quoted_tweet.get('__typename') != 'TweetTombstone':
                quoted_user = User(
                    client, quoted_tweet['core']['user_results']['result']
                )
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

        note_tweet_results = find_dict(data, 'note_tweet_results')
        if note_tweet_results:
            self.full_text: str = find_dict(note_tweet_results, 'text')[0]
        else:
            self.full_text = None

        self.is_quote_status: bool = legacy['is_quote_status']
        self.possibly_sensitive: bool = legacy.get('possibly_sensitive')
        self.possibly_sensitive_editable: bool = legacy.get(
            'possibly_sensitive_editable')
        self.quote_count: int = legacy['quote_count']
        self.media: list = legacy['entities'].get('media')
        self.urls: list = legacy['entities'].get('urls')
        self.reply_count: int = legacy['reply_count']
        self.favorite_count: int = legacy['favorite_count']
        self.favorited: bool = legacy['favorited']
        self.view_count: int = data['views'].get('count')
        self.retweet_count: int = legacy['retweet_count']
        self.editable_until_msecs: int = data['edit_control'].get(
            'editable_until_msecs')
        self.is_translatable: bool = data.get('is_translatable')
        self.is_edit_eligible: bool = data['edit_control'].get(
            'is_edit_eligible')
        self.edits_remaining: int = data['edit_control'].get('edits_remaining')
        self.state: str = data['views'].get('state')
        self.has_community_notes: bool = data.get('has_birdwatch_notes')

        if 'birdwatch_pivot' in data:
            community_note_data = data['birdwatch_pivot']
            self.community_note = {
                'id': community_note_data['note']['rest_id'],
                'text': community_note_data['subtitle']['text']
            }
        else:
            self.community_note = None

        if note_tweet_results:
            hashtags_ = find_dict(note_tweet_results, 'hashtags')
            if hashtags_:
                hashtags = hashtags_[0]
            else:
                hashtags = []
        else:
            hashtags = legacy['entities'].get('hashtags', [])
        self.hashtags: list[str] = [
            i['text'] for i in hashtags
        ]

        if (
            'card' in data and
            data['card']['legacy']['name'].startswith('poll')
        ):
            self._poll_data = data['card']
        else:
            self._poll_data = None

    @property
    def created_at_datetime(self) -> datetime:
        return timestamp_to_datetime(self.created_at)

    @property
    def poll(self) -> Poll:
        return self._poll_data and Poll(self._client, self._poll_data, self)

    def delete(self) -> Response:
        """Deletes the tweet.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.

        Examples
        --------
        >>> tweet.delete()
        """
        return self._client.delete_tweet(self.id)

    def favorite(self) -> Response:
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
        return self._client.favorite_tweet(self.id)

    def unfavorite(self) -> Response:
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
        return self._client.unfavorite_tweet(self.id)

    def retweet(self) -> Response:
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
        return self._client.retweet(self.id)

    def delete_retweet(self) -> Response:
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
        return self._client.delete_retweet(self.id)

    def bookmark(self) -> Response:
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
        return self._client.bookmark_tweet(self.id)

    def delete_bookmark(self) -> Response:
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
        return self._client.delete_bookmark(self.id)

    def reply(
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
        >>> tweet.reply(
        ...     tweet_text,
        ...     media_ids=media_ids
        ... )

        See Also
        --------
        `Client.upload_media`
        """
        return self._client.create_tweet(
            text, media_ids, reply_to=self.id, **kwargs
        )

    def get_retweeters(
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
        return self._client.get_retweeters(self.id, count, cursor)

    def get_favoriters(
        self, count: str = 40, cursor: str | None = None
    ) -> Result[User]:
        """
        Retrieve users who favorited a specific tweet.

        Parameters
        ----------
        tweet_id : :class:`str`
            The ID of the tweet.
        count : int, default=40
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
        return self._client.get_favoriters(self.id, count, cursor)

    def update(self) -> None:
        new = self._client.get_tweet_by_id(self.id)
        self.__dict__.update(new.__dict__)

    def __repr__(self) -> str:
        return f'<Tweet id="{self.id}">'

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, Tweet) and self.id == __value.id

    def __ne__(self, __value: object) -> bool:
        return not self == __value


class ScheduledTweet:
    def __init__(self, client: Client, data: dict) -> None:
        self._client = client

        self.id = data['rest_id']
        self.execute_at: int = data['scheduling_info']['execute_at']
        self.state: str = data['scheduling_info']['state']
        self.type: str = data['tweet_create_request']['type']
        self.text: str = data['tweet_create_request']['status']
        self.media = [i['media_info'] for i in data.get('media_entities', [])]

    def delete(self) -> Response:
        """
        Delete the scheduled tweet.

        Returns
        -------
        :class:`httpx.Response`
            Response returned from twitter api.
        """
        return self._client.delete_scheduled_tweet(self.id)

    def __repr__(self) -> str:
        return f'<ScheduledTweet id="{self.id}">'

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, ScheduledTweet) and self.id == __value.id

    def __ne__(self, __value: object) -> bool:
        return not self == __value


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


# @dataclass
# class 


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
            choice_count = binding_values[f'choice{i}_count']
            choices.append({
                'number': str(i),
                'label': choice_label['string_value'],
                'count': choice_count.get('string_value', '0')
            })

        self.choices = choices

        duration_minutes = binding_values['duration_minutes']['string_value']
        self.duration_minutes = int(duration_minutes)

        end = binding_values['end_datetime_utc']['string_value']
        updated = binding_values['last_updated_datetime_utc']['string_value']
        self.end_datetime_utc: str = end
        self.last_updated_datetime_utc: str = updated

        counts_are_final = binding_values['counts_are_final']['boolean_value']
        self.counts_are_final: bool = counts_are_final

        if 'selected_choice' in binding_values:
            selected_choice = binding_values['selected_choice']['string_value']
            self.selected_choice: str = selected_choice
        else:
            self.selected_choice = None

    def vote(self, selected_choice: str) -> Poll:
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
        return self._client.vote(
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

    def update(self) -> None:
        new = self._client.get_community_note(self.id)
        self.__dict__.update(new.__dict__)

    def __repr__(self) -> str:
        return f'<CommunityNote id="{self.id}">'

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, CommunityNote) and self.id == __value.id

    def __ne__(self, __value: object) -> bool:
        return not self == __value
