<img src="https://i.imgur.com/VbAcRG5.jpg" width="500">

# Twikit
A simple API wrapper to interact with twitter's internal API.
Read the documentation for more information.
- [Documentation (English)](https://twikit.readthedocs.io/en/latest/twikit.html)

## Features
### No API Key Required
The library uses an unofficial API and therefore does **not require an API key**.
### Completely Free
The service is entirely free to use.

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

For more examples, see [example.py](https://github.com/d60/twikit/blob/main/example.py).

## Contributing
This project is currently in beta, and we would love to hear your thoughts and suggestions.
If you have any features you'd like to see added or encounter any issues,
please let us know in the [issues](https://github.com/d60/twikit/issues) section.

Additionally, if you find this library useful, spreading the word by starring it would be greatly appreciated and serve as motivation for further development. Thank you!