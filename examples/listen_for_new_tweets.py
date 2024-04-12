import time
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


def get_latest_tweet() -> Tweet:
    return client.get_user_tweets(USER_ID, 'Replies')[0]


def main() -> NoReturn:
    before_tweet = get_latest_tweet()

    while True:
        time.sleep(CHECK_INTERVAL)
        latest_tweet = get_latest_tweet()
        if (
            before_tweet != latest_tweet and
            before_tweet.created_at_datetime < latest_tweet.created_at_datetime
        ):
            callable(latest_tweet)
        before_tweet = latest_tweet

main()
