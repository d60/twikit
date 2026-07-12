> [!IMPORTANT]
> ## This is an unofficial community patch fork
> This fork exists because [d60/twikit](https://github.com/d60/twikit) broke
> against X's current frontend (`Exception: Couldn't get KEY_BYTE indices`,
> see [#408](https://github.com/d60/twikit/issues/408) /
> [#409](https://github.com/d60/twikit/issues/409)) and, as of this writing,
> no fix has been merged/released to PyPI.
>
> **What's fixed here, on top of the latest `d60/twikit` release:**
> - `ondemand.s` webpack-chunk regex updated to match X's current bundle
>   format, adapted from community PR
>   [d60/twikit#411](https://github.com/d60/twikit/pull/411) by
>   [@ryanstoic](https://github.com/ryanstoic), plus hardening so the hash
>   lookup accepts both single- and double-quoted values (the original PR
>   only handled double quotes).
> - `User.description_urls`, `User.withheld_in_countries`, and
>   `User.pinned_tweet_ids` (both the authenticated and guest-mode `User`
>   classes) now tolerate X omitting those fields from the response,
>   instead of raising `KeyError`. `pinned_tweet_ids_str` in particular is
>   commonly missing for accounts that have never pinned a tweet
>   (observed on several corporate/official accounts).
>
> **Install this fork directly:**
> ```
> pip install git+https://github.com/leslienwu/twikit-patched.git@fix/ondemand-key-byte-indices-2026
> ```
>
> This is a personal patch maintained on a best-effort basis, not a
> long-term fork of the project — if/when these fixes (or better ones) land
> upstream in `d60/twikit`, prefer that instead.

> [!NOTE]
> https://github.com/d60/twitter_login (under development)

<img src="https://i.imgur.com/iJe6rsZ.png"  width="500">



![Number of GitHub stars](https://img.shields.io/github/stars/d60/twikit)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/d60/twikit)
![Version](https://img.shields.io/pypi/v/twikit?label=PyPI)
[![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Create%20your%20own%20Twitter%20bot%20for%20free%20with%20%22Twikit%22!%20%23python%20%23twitter%20%23twikit%20%23programming%20%23github%20%23bot&url=https%3A%2F%2Fgithub.com%2Fd60%2Ftwikit)
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/nCrByrr8cX)
[![BuyMeACoffee](https://img.shields.io/badge/-buy_me_a%C2%A0coffee-gray?logo=buy-me-a-coffee)](https://www.buymeacoffee.com/d60py)

[[日本語](https://github.com/d60/twikit/blob/main/README-ja.md)]
[[中文](https://github.com/d60/twikit/blob/main/README-zh.md)]


# Twikit <img height="35"  src="https://i.imgur.com/9HSdIl4.png"  valign="bottom">

A Simple Twitter API Scraper

You can use functions such as posting or searching for tweets without an API key using this library.

- [Documentation (English)](https://twikit.readthedocs.io/en/latest/twikit.html)


🔵 [Discord](https://discord.gg/nCrByrr8cX)

> [!NOTE]
> Released twikit_grok an extension for using Grok AI with Twikit.  
> For more details, visit: https://github.com/d60/twikit_grok.




## Features

### No API Key Required

This library uses scraping and does not require an API key.

### Free

This library is free to use.


## Functionality

By using Twikit, you can access functionalities such as the following:

-  Create tweets

-  Search tweets

-  Retrieve trending topics

- etc...



## Installing

```bash

pip install twikit

```



## Quick Example

**Define a client and log in to the account.**

```python
import asyncio
from twikit import Client

USERNAME = 'example_user'
EMAIL = 'email@example.com'
PASSWORD = 'password0000'

# Initialize client
client = Client('en-US')

async def main():
    await client.login(
        auth_info_1=USERNAME,
        auth_info_2=EMAIL,
        password=PASSWORD,
        cookies_file='cookies.json'
    )

asyncio.run(main())
```

**Create a tweet with media attached.**

```python
# Upload media files and obtain media_ids
media_ids = [
    await client.upload_media('media1.jpg'),
    await client.upload_media('media2.jpg')
]

# Create a tweet with the provided text and attached media
await client.create_tweet(
    text='Example Tweet',
    media_ids=media_ids
)

```

**Search the latest tweets based on a keyword**
```python
tweets = await client.search_tweet('python', 'Latest')

for tweet in tweets:
    print(
        tweet.user.name,
        tweet.text,
        tweet.created_at
    )
```

**Retrieve user tweets**
```python
tweets = await client.get_user_tweets('123456', 'Tweets')

for tweet in tweets:
    print(tweet.text)
```

**Send a dm**
```python
await client.send_dm('123456789', 'Hello')
```

**Get trends**
```python
await client.get_trends('trending')
```

More Examples: [examples](https://github.com/d60/twikit/tree/main/examples) <br>

## Contributing

If you encounter any bugs or issues, please report them on [issues](https://github.com/d60/twikit/issues).


If you find this library useful, consider starring this repository⭐️
