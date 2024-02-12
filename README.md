<img src="https://i.imgur.com/iJe6rsZ.png" width="510">

![Number of GitHub stars](https://img.shields.io/github/stars/d60/twikit)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/d60/twikit)

# Twikit <img height="35" src="https://i.imgur.com/9HSdIl4.png" valign="bottom">
A simple API wrapper to interact with twitter's internal API.
- [Documentation (English)](https://twikit.readthedocs.io/en/latest/twikit.html)
- [Async Documentation](https://twikit.readthedocs.io/en/latest/twikit.twikit_async.html)

If you have any questions, please ask on [Reddit](https://www.reddit.com/r/Python/comments/1aj53tt/twitter_api_wrapper_for_python_without_api_keys/) or [Discord](https://discord.gg/nCrByrr8cX).

## Features
### No API Key Required
The library uses an unofficial API and therefore does **not require an API key**.
### Completely Free
The service is entirely free to use.
### Both Synchronous and Asynchronous Support
Whether you prefer **synchronous** or **asynchronous** programming,
Twikit supports both, providing flexibility for different use cases.

## Functionality
This library allows you to perform various Twitter-related actions, including:
- **Create tweets**
- **Search tweets**
- **Retrieve trending topics**
- etc...

## Installing
 ```back
 pip install twikit
 ```

## Quick Example
**Define a client and log in to the account.**
```python
from twikit import Client

USERNAME = 'example_user'
EMAIL = 'email@example.com'
PASSWORD = 'password0000'

# Initialize client
client = Client('en-US')
# Login to the service with provided user credentials
client.login(
    auth_info_1=USERNAME ,
    auth_info_2=EMAIL,
    password=PASSWORD
)
```
**Create a tweet with media attached.**
```python
# Upload media files and obtain media_ids
media_ids = [
    client.upload_media('media1.jpg', index=0),
    client.upload_media('media2.jpg', index=1)
]
# Create a tweet with the provided text and attached media
client.create_tweet(
    text='Example Tweet',
    media_ids=media_ids
)
```

More Examples: [example.py](https://github.com/d60/twikit/blob/main/example.py) <br>
Async Examples: [example_async.py](https://github.com/d60/twikit/blob/main/example_async.py) <br>
Rate Limits: [ratelimits.md](https://github.com/d60/twikit/blob/main/ratelimits.md)

## Contributing
I would like to hear your thoughts and suggestions.
If you have any features you'd like to see added or encounter any issues,
please let me know in the [issues](https://github.com/d60/twikit/issues) section.

Additionally, if you find this library useful, I would appreciate it if you would star this repository or share this library! Thank you very much!
