# Twikit Guest Client

This directory contains the `GuestClient`, a specialized client for interacting with the Twitter API without authentication. It allows you to access publicly available information on Twitter as a guest user.

## The `GuestClient` Class

The `GuestClient` is designed for read-only access to Twitter data. It does not require a username and password, but it has a more limited set of features compared to the authenticated `Client`.

### Initialization and Activation

To use the `GuestClient`, you first need to create an instance of it and then activate it to generate a guest token.

```python
import asyncio
from twikit.guest import GuestClient

async def main():
    # Initialize the guest client
    client = GuestClient()

    # Activate the client to get a guest token
    await client.activate()

    # You can now use the guest client to access public Twitter data
    # For example, to get a user's profile:
    user = await client.get_user_by_screen_name('TwitterDev')
    print(f'User: {user.name} (@{user.screen_name})')

if __name__ == '__main__':
    asyncio.run(main())
```

### Key Methods

The `GuestClient` provides the following methods for accessing public Twitter data:

- `get_user_by_screen_name(screen_name)`: Retrieves a user's profile by their screen name.
- `get_user_by_id(user_id)`: Retrieves a user's profile by their user ID.
- `get_user_tweets(user_id, count=40)`: Retrieves a user's most recent tweets.
- `get_tweet_by_id(tweet_id)`: Retrieves a specific tweet by its ID.
- `get_user_highlights_tweets(user_id, count=20)`: Retrieves a user's highlighted tweets.

### Limitations

The `GuestClient` has the following limitations:

- **Read-Only**: It can only be used to read data. You cannot create, delete, or modify content (e.g., you cannot tweet, follow, or send DMs).
- **Limited Scope**: It can only access publicly available information. You cannot access protected tweets or other private data.
- **Fewer Features**: It does not support many of the advanced features of the authenticated client, such as timelines, lists, communities, and streaming.

The `GuestClient` is ideal for applications that only need to access public Twitter data without the need for a user account. For more advanced features and to interact with Twitter as a specific user, you should use the main `Client`.
