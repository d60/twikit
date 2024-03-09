<img src="https://i.imgur.com/iJe6rsZ.png" width="500">

![Number of GitHub stars](https://img.shields.io/github/stars/d60/twikit)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/d60/twikit)
![Version](https://img.shields.io/pypi/v/twikit?label=PyPI)
[![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Create%20your%20own%20Twitter%20bot%20for%20free%20with%20%22Twikit%22!%20%23python%20%23twitter%20%23twikit%20%23programming%20%23github%20%23bot&url=https%3A%2F%2Fgithub.com%2Fd60%2Ftwikit)
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/nCrByrr8cX)


# Twikit <img height="35" src="https://i.imgur.com/9HSdIl4.png" valign="bottom">
simple API wrapper to interact with twitter's unofficial API.
You can log in to Twitter using your account username, email address and password and use most features on Twitter, such as posting and retrieving tweets, liking and following users.
- [Documentation (English)](https://twikit.readthedocs.io/en/latest/twikit.html)
- [Async Documentation](https://twikit.readthedocs.io/en/latest/twikit.twikit_async.html)

If you have any questions, please ask on [Discord](https://discord.gg/nCrByrr8cX).

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

More Examples: [examples](https://github.com/d60/twikit/tree/main/examples) <br>

## Contributing
I would like to hear your thoughts and suggestions.
If you have any features you'd like to see added or encounter any issues,
please let me know in the [issues](https://github.com/d60/twikit/issues) section.

Additionally, if you find this library useful, I would appreciate it if you would star this repository or share this library⭐! Thank you very much!
