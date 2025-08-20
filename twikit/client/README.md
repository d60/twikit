# Twikit Client

This directory contains the main `Client` class, which is the primary interface for interacting with the Twitter API through the `twikit` library.

## The `Client` Class

The `Client` class is responsible for managing your session, handling authentication, and making requests to the Twitter API. It provides a comprehensive set of methods for performing various actions on Twitter.

### Initialization

To use the client, you first need to create an instance of it:

```python
from twikit import Client

client = Client(language='en-US')
```

The `Client` constructor accepts the following parameters:

- `language` (str, optional): The language to use for API requests. Defaults to `'en-US'`.
- `proxy` (str, optional): The URL of a proxy server to use for requests.
- `captcha_solver` (Capsolver, optional): An instance of a CAPTCHA solver to handle login challenges.
- `user_agent` (str, optional): A custom user agent to use for requests.

### Authentication

The primary method for authentication is `login()`:

```python
await client.login(
    auth_info_1='your_username',
    auth_info_2='your_email@example.com',
    password='your_password'
)
```

The `login()` method supports various authentication scenarios, including 2FA and cookie-based sessions.

### Key Methods

The `Client` class provides a wide range of methods for interacting with Twitter. Here are some of the key methods:

- **Tweet Management**:
  - `create_tweet()`: Creates a new tweet.
  - `delete_tweet()`: Deletes a tweet.
  - `get_tweet_by_id()`: Retrieves a tweet by its ID.
  - `search_tweet()`: Searches for tweets.
  - `favorite_tweet()`: Favorites a tweet.
  - `retweet()`: Retweets a tweet.

- **User Management**:
  - `get_user_by_id()`: Retrieves a user by their ID.
  - `get_user_by_screen_name()`: Retrieves a user by their screen name.
  - `search_user()`: Searches for users.
  - `follow_user()`: Follows a user.
  - `unfollow_user()`: Unfollows a user.

- **Direct Messages**:
  - `send_dm()`: Sends a direct message to a user.
  - `get_dm_history()`: Retrieves the direct message history with a user.
  - `delete_dm()`: Deletes a direct message.

- **Timelines**:
  - `get_timeline()`: Retrieves the main "For You" timeline.
  - `get_latest_timeline()`: Retrieves the "Following" timeline.
  - `get_user_tweets()`: Retrieves a user's tweets.

- **Lists**:
  - `create_list()`: Creates a new list.
  - `get_list()`: Retrieves a list by its ID.
  - `get_list_tweets()`: Retrieves the tweets from a list.

- **Communities**:
  - `get_community()`: Retrieves a community by its ID.
  - `get_community_tweets()`: Retrieves the tweets from a community.
  - `join_community()`: Joins a community.

- **Bookmarks**:
  - `get_bookmarks()`: Retrieves the user's bookmarks.
  - `bookmark_tweet()`: Bookmarks a tweet.

- **Streaming API**:
  - `get_streaming_session()`: Creates a session for real-time streaming of Twitter events.

For a complete list of methods and their parameters, please refer to the source code in `client.py`. The examples in the `examples` directory also provide practical demonstrations of how to use these methods.

## Under the Hood: The Client's Inner Workings

The `Client` class is more than just a collection of methods. It's a sophisticated engine that simulates a browser's interaction with Twitter. Here's a closer look at some of its key internal mechanisms:

### The Authentication Flow

The `login()` method is one of the most complex parts of the library. It doesn't just send your credentials to a login endpoint. Instead, it follows a multi-step "flow" that Twitter's web app uses. This involves:
1.  **Initializing a Flow**: The client starts a login flow and gets a "flow token".
2.  **Submitting User Information**: It submits the username/email in one step.
3.  **Submitting Password**: It submits the password in a separate step.
4.  **Handling Challenges**: If Twitter requires 2FA or a CAPTCHA, the flow has steps for these challenges. The client can handle 2FA with a TOTP secret and can integrate with a CAPTCHA solver.
5.  **Executing JavaScript**: A crucial step in the flow is executing a piece of obfuscated JavaScript that Twitter uses to collect "UI metrics". `twikit` uses the `Js2Py` library to run this JavaScript and send the result back to Twitter, making the login attempt appear more legitimate.

### `GQLClient` and `V11Client`

The `Client` delegates the actual API requests to two internal clients:
-   **`GQLClient`**: This client is responsible for making requests to Twitter's internal GraphQL API. GraphQL is a modern query language for APIs that allows the client to request exactly the data it needs. Most of the newer features of Twitter are accessed through this API.
-   **`V11Client`**: This client interacts with an older, v1.1-like internal API. It's used for some of the more traditional API endpoints that haven't been migrated to GraphQL.

By using both of these internal clients, `twikit` can access a wide range of Twitter's features.

### `X-Client-Transaction-Id`

You may notice in the code that the client adds an `X-Client-Transaction-Id` header to its requests. This is a unique ID that is generated for each "transaction" (a sequence of related actions). Twitter likely uses this header to track and analyze user behavior on their platform. By generating and sending this header, `twikit` further mimics the behavior of the official web client.

### The Streaming API

The `get_streaming_session()` method provides access to Twitter's real-time data stream. This is not a simple polling mechanism. Instead, it establishes a persistent connection to a Twitter endpoint (likely using a long-polling HTTP request). Twitter will then push data down this connection as events occur (e.g., a new DM is received, a tweet's engagement stats change). This is a much more efficient way to get real-time updates than repeatedly polling for changes.
