import asyncio
from typing import NoReturn

from twikit import Client, Tweet

AUTH_INFO_1 = '...'
AUTH_INFO_2 = '...'
PASSWORD = '...'

client = Client()

USER_ID = '44196397'
CHECK_INTERVAL = 60 * 5


def callback(tweet: Tweet) -> None:
    print(f'New tweet posted : {tweet.text}')


async def get_latest_tweet() -> Tweet:
    return (await client.get_user_tweets(USER_ID, 'Replies'))[0]


async def main() -> NoReturn:
    before_tweet = await get_latest_tweet()

    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        latest_tweet = await get_latest_tweet()
        if (
            before_tweet != latest_tweet and
            before_tweet.created_at_datetime < latest_tweet.created_at_datetime
        ):
            callable(latest_tweet)
        before_tweet = latest_tweet

asyncio.run(main())
