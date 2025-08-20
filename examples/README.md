# Twikit Examples

This directory contains a collection of example scripts that demonstrate how to use the `twikit` library for various tasks. These examples are a great way to learn about the library's features and how to use them in your own projects.

## Running the Examples

Before running the examples, make sure you have `twikit` installed:

```bash
pip install twikit
```

You will also need to provide your Twitter account credentials in the scripts that require authentication. Look for the following variables at the top of the files and replace the placeholder values with your own information:

```python
USERNAME = 'your_username'
EMAIL = 'your_email@example.com'
PASSWORD = 'your_password'
```

## Example Scripts

Here is a brief description of each example script:

### `example.py`

This is a comprehensive example that demonstrates many of the core features of the `twikit` library. It shows how to:
- Log in to your account.
- Search for tweets and users.
- Get user profiles and tweets.
- Follow and unfollow users.
- Send direct messages with media.
- Get DM history.
- Get a tweet by its ID.
- Like, retweet, and reply to tweets.
- Create tweets with media and polls.
- Get trending topics.

This script is a great starting point for understanding the overall functionality of the library.

### `delete_all_tweets.py`

This script demonstrates how to delete all of a user's tweets and replies. It fetches all of the user's posts and then deletes them concurrently for efficiency.

### `dm_auto_reply.py`

This script shows how to build a simple bot that automatically replies to direct messages from a specific user. It uses the streaming API to listen for new DMs in real-time.

### `download_tweet_media.py`

This script demonstrates how to download media (photos, videos, and GIFs) from a tweet. It gets a tweet by its ID and then iterates through the media objects, downloading each one.

### `guest.py`

This script shows how to use the `GuestClient` to access public Twitter data without authentication. It demonstrates how to:
- Get a user's profile by their screen name or ID.
- Get a user's most recent tweets.
- Get a specific tweet by its ID.

### `listen_for_new_tweets.py`

This script provides a simple example of how to monitor a user for new tweets. It uses a polling mechanism to periodically check the user's latest tweet and detect when a new one has been posted.

These examples are designed to be simple and easy to understand. You can use them as a basis for your own projects or as a reference for how to use the various features of the `twikit` library.
