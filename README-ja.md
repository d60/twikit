<img  src="https://i.imgur.com/iJe6rsZ.png"  width="500">



![Number of GitHub stars](https://img.shields.io/github/stars/d60/twikit)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/d60/twikit)
![Version](https://img.shields.io/pypi/v/twikit?label=PyPI)
[![Tweet](https://img.shields.io/twitter/url/http/shields.io.svg?style=social)](https://twitter.com/intent/tweet?text=Create%20your%20own%20Twitter%20bot%20for%20free%20with%20%22Twikit%22!%20%23python%20%23twitter%20%23twikit%20%23programming%20%23github%20%23bot&url=https%3A%2F%2Fgithub.com%2Fd60%2Ftwikit)
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/nCrByrr8cX)
[![BuyMeACoffee](https://img.shields.io/badge/-buy_me_a%C2%A0coffee-gray?logo=buy-me-a-coffee)](https://www.buymeacoffee.com/d60py)

[[English](https://github.com/d60/twikit/blob/main/README.md)]
[[中文](https://github.com/d60/twikit/blob/main/README-zh.md)]

# Twikit <img height="35"  src="https://i.imgur.com/9HSdIl4.png"  valign="bottom">

このライブラリを使用することで、APIキーなしで、ツイートの投稿や検索などの機能を使用することができます。

- [ドキュメント](https://twikit.readthedocs.io/en/latest/twikit.html)

- [非同期ドキュメント](https://twikit.readthedocs.io/en/latest/twikit.twikit_async.html)

[Discord](https://discord.gg/nCrByrr8cX)



## 特徴

### APIキー不要

このライブラリは、ツイッターの非公式APIを使用しているため、APIキーは必要ありません。

### 無料

このライブラリは、無料で使用することができます。

### 同期と非同期の両方に対応

同期と非同期の両方に対応しています。


## 機能

このライブラリを使用することで、

-  ツイートの投稿

-  ツイートの検索

-  トレンドの取得

などのさまざまな機能を使用することができます。



## インストール

```bash

pip install twikit

```


## 使用例

**クライアントを定義し、アカウントにログインする。**

```python
from twikit import Client

USERNAME = 'example_user'
EMAIL = 'email@example.com'
PASSWORD = 'password0000'

# Initialize client
client = Client('en-US')

# アカウントにログイン
client.login(
    auth_info_1=USERNAME ,
    auth_info_2=EMAIL,
    password=PASSWORD
)
```

**メディア付きツイートを作成する。**

```python
# メディアをアップロードし、メディアIDを取得する。
media_ids = [
    client.upload_media('media1.jpg'),
    client.upload_media('media2.jpg')
]

# ツイートを投稿する
client.create_tweet(
    text='Example Tweet',
    media_ids=media_ids
)

```

**ツイートを検索する**
```python
tweets = client.search_tweet('python', 'Latest')

for tweet in tweets:
    print(
        tweet.user.name,
        tweet.text,
        tweet.created_at
    )
```

**ユーザーのツイートを取得する**
```python
tweets = client.get_user_tweets('123456', 'Tweet')

for tweet in tweets:
    print(tweet.text)
```

[examples](https://github.com/d60/twikit/tree/main/examples)<br>
