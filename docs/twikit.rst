twikit package
==============

.. automodule:: twikit
   :members:
   :undoc-members:

Client
--------------------

.. autoclass:: twikit.client.client.Client
   :members:
   :undoc-members:
   :member-order: bysource

Tweet
-------------------

.. automodule:: twikit.tweet
   :members:
   :exclude-members: TweetTombstone
   :member-order: bysource

User
------------------

.. automodule:: twikit.user
   :members:
   :undoc-members:
   :member-order: bysource

Message
---------------------

.. automodule:: twikit.message
   :members:
   :undoc-members:
   :member-order: bysource

Streaming
---------------------

With the streaming API, you can receive real-time events such as tweet engagements,
DM updates, and DM typings. The basic procedure involves looping through the
stream session obtained with :attr:`.Client.get_streaming_session` and, if necessary,
updating the topics to be streamed using :attr:`.StreamingSession.update_subscriptions`.

Example Code:

.. code-block:: python

   from twikit.streaming import Topic

   topics = {
       Topic.tweet_engagement('1739617652'), # Stream tweet engagement
       Topic.dm_update('17544932482-174455537996'), # Stream DM update
       Topic.dm_typing('17544932482-174455537996') # Stream DM typing
   }
   session = client.get_streaming_session(topics)

   for topic, payload in session:
       if payload.dm_update:
           conversation_id = payload.dm_update.conversation_id
           user_id = payload.dm_update.user_id
           print(f'{conversation_id}: {user_id} sent a message')

       if payload.dm_typing:
           conversation_id = payload.dm_typing.conversation_id
           user_id = payload.dm_typing.user_id
           print(f'{conversation_id}: {user_id} is typing')

       if payload.tweet_engagement:
           like = payload.tweet_engagement.like_count
           retweet = payload.tweet_engagement.retweet_count
           view = payload.tweet_engagement.view_count
           print(f'Tweet engagement updated likes: {like} retweets: {retweet} views: {view}')

.. automodule:: twikit.streaming
   :members:
   :undoc-members:
   :member-order: bysource

Media
-------------------

.. autoclass:: twikit.media.Media
   :undoc-members:
   :member-order: bysource

.. autoclass:: twikit.media.Photo
   :show-inheritance:
   :undoc-members:
   :member-order: bysource

.. autoclass:: twikit.media.Video
   :show-inheritance:
   :undoc-members:
   :member-order: bysource
   :members: get_subtitles

.. autoclass:: twikit.media.AnimatedGif
   :show-inheritance:
   :undoc-members:
   :member-order: bysource

.. autoclass:: twikit.media.Stream
   :undoc-members:
   :member-order: bysource
   :members: get, download


Trend
-------------------

.. automodule:: twikit.trend
   :members:
   :undoc-members:
   :member-order: bysource

List
-------------------

.. autoclass:: twikit.list.List
   :members:
   :undoc-members:
   :member-order: bysource

Community
-------------------

.. automodule:: twikit.community
   :members:
   :undoc-members:
   :member-order: bysource

Notification
-------------------

.. autoclass:: twikit.notification.Notification
   :members:
   :undoc-members:
   :member-order: bysource

Geo
-------------------

.. autoclass:: twikit.geo.Place
   :members:
   :undoc-members:
   :member-order: bysource

Capsolver
-------------------

.. autoclass:: twikit._captcha.capsolver.Capsolver
   :members:
   :undoc-members:
   :member-order: bysource
   :exclude-members: create_task,get_task_result,solve_funcaptcha

Utils
-------------------

.. autoclass:: twikit.utils.Result
   :members:
   :undoc-members:
   :member-order: bysource

Errors
--------------------

.. automodule:: twikit.errors
   :members:
   :undoc-members:
   :member-order: bysource
