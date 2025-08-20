# Twikit Data Models

The `twikit` library uses a set of data models to represent Twitter data in a structured and object-oriented way. These models provide a convenient interface for accessing the attributes of Twitter objects and performing actions on them.

The main data models are:
- `Tweet`
- `User`
- `Message`

## The `Tweet` Model

The `Tweet` class (`twikit/tweet.py`) represents a single tweet. It contains a wealth of information about the tweet and provides methods for interacting with it.

### Key Attributes

- `id` (str): The unique ID of the tweet.
- `text` (str): The text content of the tweet.
- `user` (User): The author of the tweet.
- `created_at` (str): The timestamp of when the tweet was created.
- `created_at_datetime` (datetime): The `created_at` timestamp converted to a `datetime` object.
- `favorite_count` (int): The number of likes the tweet has received.
- `retweet_count` (int): The number of retweets the tweet has received.
- `reply_count` (int): The number of replies to the tweet.
- `media` (list): A list of media objects (photos, videos, GIFs) attached to the tweet.
- `poll` (Poll): A `Poll` object if the tweet contains a poll.
- `quote` (Tweet): The tweet being quoted, if any.
- `retweeted_tweet` (Tweet): The original tweet, if this tweet is a retweet.

### Key Methods

- `delete()`: Deletes the tweet.
- `favorite()`: Likes the tweet.
- `unfavorite()`: Unlikes the tweet.
- `retweet()`: Retweets the tweet.
- `reply(text, media_ids)`: Replies to the tweet.
- `get_retweeters()`: Gets a list of users who retweeted the tweet.
- `get_favoriters()`: Gets a list of users who liked the tweet.

## The `User` Model

The `User` class (`twikit/user.py`) represents a single Twitter user. It contains information about the user's profile and provides methods for interacting with them.

### Key Attributes

- `id` (str): The unique ID of the user.
- `name` (str): The display name of the user.
- `screen_name` (str): The user's handle (e.g., `@twitter`).
- `description` (str): The user's profile bio.
- `followers_count` (int): The number of followers the user has.
- `following_count` (int): The number of users the user is following.
- `statuses_count` (int): The number of tweets the user has posted.
- `profile_image_url` (str): The URL of the user's profile image.
- `profile_banner_url` (str): The URL of the user's profile banner.
- `is_blue_verified` (bool): Whether the user has a blue checkmark.

### Key Methods

- `get_tweets(tweet_type)`: Gets the user's tweets.
- `follow()`: Follows the user.
- `unfollow()`: Unfollows the user.
- `block()`: Blocks the user.
- `unblock()`: Unblocks the user.
- `mute()`: Mutes the user.
- `unmute()`: Unmutes the user.
- `send_dm(text, media_id)`: Sends a direct message to the user.
- `get_dm_history()`: Gets the DM history with the user.
- `get_followers()`: Gets a list of the user's followers.
- `get_following()`: Gets a list of users the user is following.

## The `Message` Model

The `Message` class (`twikit/message.py`) represents a single direct message.

### Key Attributes

- `id` (str): The unique ID of the message.
- `text` (str): The text content of the message.
- `time` (str): The timestamp of when the message was sent.
- `sender_id` (str): The ID of the user who sent the message.
- `recipient_id` (str): The ID of the user who received the message.
- `attachment` (dict): Information about any media attached to the message.

### Key Methods

- `delete()`: Deletes the message.
- `reply(text, media_id)`: Replies to the message.
- `add_reaction(emoji)`: Adds a reaction to the message.
- `remove_reaction(emoji)`: Removes a reaction from the message.

## Data Handling Concepts

### The Power of Data Models

When `twikit` receives data from the Twitter API, it comes in the form of complex, nested JSON. While it's possible to work with this raw data directly, it can be cumbersome and error-prone. This is where data models come in.

`twikit` parses the raw JSON and uses it to construct instances of its data model classes (`Tweet`, `User`, etc.). This has several advantages:

-   **Ease of Use**: Accessing data is as simple as accessing an object's attribute (e.g., `tweet.text`) rather than navigating a dictionary (e.g., `tweet_data['legacy']['full_text']`).
-   **Discoverability**: With an object, you can easily see all the available attributes and methods, which is much harder with a raw dictionary.
-   **Convenience Methods**: The models include methods for performing actions related to the object (e.g., `tweet.favorite()`). This makes the library more intuitive and object-oriented.
-   **Data Cleaning and Formatting**: The models can clean and format the data, for example, by converting timestamps into `datetime` objects.

### Handling Pagination with the `Result` Class

Many API endpoints return lists of items (e.g., a list of tweets, a list of followers). These lists are often too long to be returned in a single response, so they are "paginated". Twitter's internal API uses a "cursor-based" pagination system.

Instead of just returning a list of `Tweet` or `User` objects, methods that return paginated results in `twikit` return an instance of the `Result` class. This class is a wrapper around the list of results that also contains the "cursor" needed to fetch the next page of results.

The `Result` object has a `next()` method that automatically makes another API request to fetch the next page of results. This provides a simple and elegant way to work with paginated data:

```python
# Get the first page of tweets
tweets = await user.get_tweets('Tweets')

# Get the next page
more_tweets = await tweets.next()
```

This abstraction saves you from having to manually manage cursors and construct API requests for each page of results.

These data models are central to the `twikit` library and provide a powerful and intuitive way to work with Twitter data. For more details on each model, please refer to their respective source files.
