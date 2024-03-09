import asyncio
import time

from twikit.twikit_async import Client

AUTH_INFO_1 = '...'
AUTH_INFO_2 = '...'
PASSWORD = '...'

client = Client('en-US')


async def main():
    started_time = time.time()

    client.load_cookies('cookies.json')
    client_user = await client.user()

    # Get all posts
    all_tweets = []
    tweets = await client_user.get_tweets('Replies')
    all_tweets += tweets

    while len(tweets) != 0:
        tweets = await tweets.next()
        all_tweets += tweets

    tasks = []
    for tweet in all_tweets:
        tasks.append(tweet.delete())

    gather = asyncio.gather(*tasks)
    await gather

    print(
        f'Deleted {len(all_tweets)} tweets\n'
        f'Time: {time.time() - started_time}'
    )

asyncio.run(main())
