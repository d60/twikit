# Twikit Library

This directory contains the core source code for the `twikit` library, a powerful Python wrapper for the Twitter API that does not require an API key.

## Architecture

The `twikit` library is designed to be an intuitive and feature-rich tool for interacting with Twitter. It achieves this by simulating a web browser's behavior to communicate with Twitter's internal APIs. The key components of the library are:

- **`client`**: The main entry point for all interactions with the library. The `Client` class handles authentication, sends requests to the Twitter API, and manages the session.
- **Data Models**: The library uses a set of data models to represent Twitter data in a structured and easy-to-use format. The main data models are:
  - `Tweet`: Represents a tweet, with all its attributes and associated actions.
  - `User`: Represents a Twitter user, with their profile information and associated actions.
  - `Message`: Represents a direct message.
- **Guest Client**: A separate client for interacting with Twitter as an unauthenticated user.
- **API Clients**: The library uses internal clients for communicating with Twitter's GraphQL (`gql.py`) and v1.1-like (`v11.py`) APIs.
- **Error Handling**: A robust system of custom exceptions to handle various errors that may occur when interacting with the API.
- **Utilities**: A collection of utility functions for various tasks, such as parsing data and handling authentication flows.

## Installation

The `twikit` library can be installed using pip:

```bash
pip install twikit
```

## Quick Start

To start using the library, you need to create an instance of the `Client` class and log in to your Twitter account.

```python
import asyncio
from twikit import Client

USERNAME = 'your_username'
EMAIL = 'your_email@example.com'
PASSWORD = 'your_password'

async def main():
    # Initialize the client
    client = Client('en-US')

    # Log in to your account
    await client.login(
        auth_info_1=USERNAME,
        auth_info_2=EMAIL,
        password=PASSWORD
    )

    # You can now use the client to interact with Twitter
    # For example, to get your own user information:
    me = await client.user()
    print(f'Logged in as: {me.name} (@{me.screen_name})')

if __name__ == '__main__':
    asyncio.run(main())
```

## Key Features

The `twikit` library provides a wide range of features, including:

- **Authentication**: A sophisticated login flow that can handle 2FA and CAPTCHAs, as well as session management using cookies.
- **Tweet Management**: Create, delete, like, retweet, and reply to tweets.
- **User Management**: Get user profiles, follow, unfollow, block, and mute users.
- **Direct Messages**: Send and receive direct messages, with support for media attachments and reactions.
- **Search**: Search for tweets and users.
- **Timelines**: Get the home timeline, user timelines, and list timelines.
- **Lists**: Create, manage, and subscribe to lists.
- **Communities**: Interact with Twitter Communities, including joining, leaving, and getting community tweets.
- **Bookmarks**: Manage your bookmarks and bookmark folders.
- **Streaming API**: Get real-time updates on tweet engagements and direct messages.
- **Guest Mode**: Access some information from Twitter without logging in.

For more detailed information on how to use the library, please refer to the documentation for the individual modules and the examples in the `examples` directory.
