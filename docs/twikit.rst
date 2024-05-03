twikit package
==============

.. automodule:: twikit
   :members:
   :undoc-members:
   :show-inheritance:

Client
--------------------

.. automodule:: twikit.client
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource

Tweet
-------------------

.. automodule:: twikit.tweet
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource

User
------------------

.. automodule:: twikit.user
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource

Message
---------------------

.. automodule:: twikit.message
   :members:
   :undoc-members:
   :show-inheritance:
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
   :show-inheritance:
   :member-order: bysource

Trend
-------------------

.. automodule:: twikit.trend
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource

List
-------------------

.. automodule:: twikit.list
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource

Community
-------------------

.. automodule:: twikit.community
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource

Notification
-------------------

.. automodule:: twikit.notification
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource


Utils
-------------------

.. automodule:: twikit.utils
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource

Errors
--------------------

.. automodule:: twikit.errors
   :members:
   :undoc-members:
   :show-inheritance:
   :member-order: bysource
