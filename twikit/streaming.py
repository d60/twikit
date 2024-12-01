from __future__ import annotations

from typing import TYPE_CHECKING, AsyncGenerator, NamedTuple

if TYPE_CHECKING:
    from .client.client import Client


class StreamingSession:
    """
    Represents a streaming session.

    Attributes
    ----------
    id : :class:`str`
        The ID or the session.
    topics : set[:class:`str`]
        The topics to stream.

    See Also
    --------
    .Client.get_streaming_session
    """
    def __init__(
        self, client: Client, session_id: str,
        stream: AsyncGenerator[Payload], topics: set[str], auto_reconnect: bool
    ) -> None:
        self._client = client
        self.id = session_id
        self._stream = stream
        self.topics = topics
        self.auto_reconnect = auto_reconnect

    async def reconnect(self) -> tuple[str, Payload]:
        """
        Reconnects the session.
        """
        stream = self._client._stream(self.topics)
        config_event = await anext(stream)
        self.id = config_event[1].config.session_id
        self._stream = stream
        return config_event

    async def update_subscriptions(
        self,
        subscribe: set[str] | None = None,
        unsubscribe: set[str] | None = None
    ) -> Payload:
        """
        Updates subscriptions for the session.

        Parameters
        ----------
        subscribe : set[:class:`str`], default=None
            Topics to subscribe to.
        unsubscribe : set[:class:`str`], default=None
            Topics to unsubscribe from.

        Examples
        --------
        >>> from twikit.streaming import Topic
        ...
        >>> subscribe_topics = {
        ...     Topic.tweet_engagement('1749528513'),
        ...     Topic.tweet_engagement('1765829534')
        ... }
        >>> unsubscribe_topics = {
        ...     Topic.tweet_engagement('17396176529'),
        ...     Topic.dm_update('17544932482-174455537996'),
        ...     Topic.dm_typing('17544932482-174455537996)'
        ... }
        >>> await session.update_subscriptions(
        ...     subscribe_topics, unsubscribe_topics
        ... )

        Note
        ----
        dm_update and dm_update cannot be added.

        See Also
        --------
        .Topic
        """
        return await self._client._update_subscriptions(
            self, subscribe, unsubscribe
        )

    async def __aiter__(self) -> AsyncGenerator[tuple[str, Payload]]:
        while True:
            async for event in self._stream:
                yield event
            if not self.auto_reconnect:
                break
            yield await self.reconnect()

    def __repr__(self) -> str:
        return f'<StreamingSession id="{self.id}">'


def _event_from_data(name: str, data: dict) -> StreamEventType:
    if name == 'config':
        session_id = data['session_id']
        subscription_ttl_millis = data['subscription_ttl_millis']
        heartbeat_millis = data['heartbeat_millis']
        return ConfigEvent(
            session_id, subscription_ttl_millis,
            heartbeat_millis
        )

    if name == 'subscriptions':
        errors = data['errors']
        return SubscriptionsEvent(errors)

    if name == 'tweet_engagement':
        like_count = data.get('like_count')
        retweet_count = data.get('retweet_count')
        quote_count = data.get('quote_count')
        reply_count = data.get('reply_count')
        view_count = None
        view_count_state = None
        if 'view_count_info' in data:
            view_count = data['view_count_info']['count']
            view_count_state = data['view_count_info']['state']
        return TweetEngagementEvent(
            like_count, retweet_count, view_count,
            view_count_state, quote_count, reply_count
        )

    if name == 'dm_update':
        conversation_id = data['conversation_id']
        user_id = data['user_id']
        return DMUpdateEvent(conversation_id, user_id)

    if name == 'dm_typing':
        conversation_id = data['conversation_id']
        user_id = data['user_id']
        return DMTypingEvent(conversation_id, user_id)


def _payload_from_data(data: dict) -> Payload:
    events = {
        name: _event_from_data(name, data)
        for (name, data) in data.items()
    }
    return Payload(**events)


class Payload(NamedTuple):
    """
    Represents a payload containing several types of events.
    """
    config: ConfigEvent | None = None  #: The configuration event.
    subscriptions: SubscriptionsEvent | None = None  #: The subscriptions event.
    tweet_engagement: TweetEngagementEvent | None = None  #: The tweet engagement event.
    dm_update: DMUpdateEvent | None = None  #: The direct message update event.
    dm_typing: DMTypingEvent | None = None  #: The direct message typing event.

    def __repr__(self) -> str:
        items = self._asdict().items()
        fields = [f'{i[0]}={i[1]}' for i in items if i[1] is not None]
        return f'Payload({" ".join(fields)})'


class ConfigEvent(NamedTuple):
    """
    Event representing configuration data.
    """
    session_id: str  #: The session ID associated with the configuration.
    subscription_ttl_millis: int  #: The time to live for the subscription.
    heartbeat_millis: int  #: The heartbeat interval in milliseconds.


class SubscriptionsEvent(NamedTuple):
    """
    Event representing subscription status.
    """
    errors: list  #: A list of errors.


class TweetEngagementEvent(NamedTuple):
    """
    Event representing tweet engagement metrics.
    """
    like_count: str | None  #: The number of likes on the tweet.
    retweet_count: str | None  #: The number of retweets of the tweet.
    view_count: str | None  #: The number of views of the tweet.
    view_count_state: str | None  #: The state of view count.
    quote_count: int | None  #: The number of quotes of the tweet.
    reply_count: int | None  # The number of Replies of the tweet.


class DMUpdateEvent(NamedTuple):
    """
    Event representing a (DM) update.
    """
    conversation_id: str  #: The ID of the conversation associated with the DM.
    user_id: str  #: ID of the user who sent the DM.


class DMTypingEvent(NamedTuple):
    """
    Event representing typing indication in a DM conversation.
    """
    conversation_id: str  #: The conversation where typing indication occurred.
    user_id: str  #: The ID of the typing user.

StreamEventType = (ConfigEvent | SubscriptionsEvent |
                   TweetEngagementEvent | DMTypingEvent | DMTypingEvent)


class Topic:
    """
    Utility class for generating topic strings for streaming.
    """
    @staticmethod
    def tweet_engagement(tweet_id: str) -> str:
        """
        Generates a topic string for tweet engagement events.

        Parameters
        ----------
        tweet_id : :class:`str`
            The ID of the tweet.

        Returns
        -------
        :class:`str`
            The topic string for tweet engagement events.
        """
        return f'/tweet_engagement/{tweet_id}'

    @staticmethod
    def dm_update(conversation_id: str) -> str:
        """
        Generates a topic string for direct message update events.

        Parameters
        ----------
        conversation_id : :class:`str`
            The ID of the conversation.
            Group ID (00000000) or partner_ID-your_ID (00000000-00000001)

        Returns
        -------
        :class:`str`
            The topic string for direct message update events.
        """
        return f'/dm_update/{conversation_id}'

    @staticmethod
    def dm_typing(conversation_id: str) -> str:
        """
        Generates a topic string for direct message typing events.

        Parameters
        ----------
        conversation_id : :class:`str`
            The ID of the conversation.
            Group ID (00000000) or partner_ID-your_ID (00000000-00000001)

        Returns
        -------
        :class:`str`
            The topic string for direct message typing events.
        """
        return f'/dm_typing/{conversation_id}'
