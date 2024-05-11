<img  src="https://i.imgur.com/iJe6rsZ.png"  width="500">



![Number of GitHub stars](https://img.shields.io/github/stars/d60/twikit)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/d60/twikit)
![Version](https://img.shields.io/pypi/v/twikit?label=PyPI)
[![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Create%20your%20own%20Twitter%20bot%20for%20free%20with%20%22Twikit%22!%20%23python%20%23twitter%20%23twikit%20%23programming%20%23github%20%23bot&url=https%3A%2F%2Fgithub.com%2Fd60%2Ftwikit)
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/nCrByrr8cX)
[![BuyMeACoffee](https://img.shields.io/badge/-buy_me_a%C2%A0coffee-gray?logo=buy-me-a-coffee)](https://www.buymeacoffee.com/d60py)


# Twikit <img height="35"  src="https://i.imgur.com/9HSdIl4.png"  valign="bottom">

简单的 Twitter API 抓取器

你可以使用这个库进行发布或搜索推文等功能，而无需 API 密钥。

- [document](https://twikit.readthedocs.io/en/latest/twikit.html)

- [async document](https://twikit.readthedocs.io/en/latest/twikit.twikit_async.html)

[Discord](https://discord.gg/nCrByrr8cX).



## 特征

### 不需要 API 密钥

该库使用刮擦技术，不需要 API 密钥。

### 免费的

您可以免费使用

### 同时支持同步和异步 

Twikit 支持同步和异步使用。


## 功能

使用 Twikit，您可以获得以下功能：

-  创建推文

-  搜索推文

-  检索热门话题

等等...



## 安装

```bash

pip install twikit

```


## 使用例

**Define a client and log in to the account.**

```python
from twikit import Client

USERNAME = 'example_user'
EMAIL = 'email@example.com'
PASSWORD = 'password0000'

# Initialize client
client = Client('en-US')

client.login(
    auth_info_1=USERNAME ,
    auth_info_2=EMAIL,
    password=PASSWORD
)
```

**创建一条附带媒体的推文。**

```python
# Upload media files and obtain media_ids
media_ids = [
    client.upload_media('media1.jpg'),
    client.upload_media('media2.jpg')
]

# Create a tweet with the provided text and attached media
client.create_tweet(
    text='Example Tweet',
    media_ids=media_ids
)

```

**搜索推文**
```python
tweets = client.search_tweet('python', 'Latest')

for tweet in tweets:
    print(
        tweet.user.name,
        tweet.text,
        tweet.created_at
    )
```

**检索用户的推文**
```python
tweets = client.get_user_tweets('123456', 'Tweet')

for tweet in tweets:
    print(tweet.text)
```

[examples](https://github.com/d60/twikit/tree/main/examples)<br>
