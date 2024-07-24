<img src="https://i.imgur.com/iJe6rsZ.png"  width="500">



![Number of GitHub stars](https://img.shields.io/github/stars/d60/twikit)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/d60/twikit)
![Version](https://img.shields.io/pypi/v/twikit?label=PyPI)
[![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Create%20your%20own%20Twitter%20bot%20for%20free%20with%20%22Twikit%22!%20%23python%20%23twitter%20%23twikit%20%23programming%20%23github%20%23bot&url=https%3A%2F%2Fgithub.com%2Fd60%2Ftwikit)
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/nCrByrr8cX)
[![BuyMeACoffee](https://img.shields.io/badge/-buy_me_a%C2%A0coffee-gray?logo=buy-me-a-coffee)](https://www.buymeacoffee.com/d60py)

[[English](https://github.com/d60/twikit/blob/main/README.md)]
[[日本語](https://github.com/d60/twikit/blob/main/README-ja.md)]

# Twikit <img height="35"  src="https://i.imgur.com/9HSdIl4.png"  valign="bottom">

一个简单的爬取 Twitter API 的客户端。

本库提供的函数允许你进行对推特的操作，如发布或搜索推文，并且无需开发者 API 密钥。

- [文档（英文）](https://twikit.readthedocs.io/en/latest/twikit.html)

[Discord 服务器](https://discord.gg/nCrByrr8cX)



## 特性

### 无需开发者 API 密钥

本库直接爬取推特的公共 API 进行请求，无需申请官方开发者密钥。

### 免费

本库无需付费。


## 功能

使用 Twikit，你可以：

-  创建推文

-  搜索推文

-  检索热门话题

- 等等...



## 安装

```bash

pip install twikit

```


## 使用样例

**定义一个客户端并登录**

```python
import asyncio
from twikit import Client

USERNAME = 'example_user'
EMAIL = 'email@example.com'
PASSWORD = 'password0000'

# 初始化客户端
client = Client('en-US')

async def main():
    await client.login(
        auth_info_1=USERNAME ,
        auth_info_2=EMAIL,
        password=PASSWORD
    )

asyncio.run(main())
```

**创建一条附带媒体的推文**

```python
# 上传媒体文件并获取媒体ID
media_ids = [
    await client.upload_media('media1.jpg'),
    await client.upload_media('media2.jpg')
]

# 创建一条带有提供的文本和附加媒体的推文
await client.create_tweet(
    text='Example Tweet',
    media_ids=media_ids
)

```

**搜索推文**
```python
tweets = await client.search_tweet('python', 'Latest')

for tweet in tweets:
    print(
        tweet.user.name,
        tweet.text,
        tweet.created_at
    )
```

**检索用户的推文**
```python
tweets = await client.get_user_tweets('123456', 'Tweet')

for tweet in tweets:
    print(tweet.text)
```

**获取趋势**
```python
await client.get_trends('trending')
```

[更多样例...](https://github.com/d60/twikit/tree/main/examples)<br>
