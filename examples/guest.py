import asyncio

from twikit.guest import GuestClient

client = GuestClient()


async def main():
    # Activate the client by generating a guest token.
    await client.activate()

    # Get user by screen name
    user = await client.get_user_by_screen_name('elonmusk')
    print(user)
    # Get user by ID
    user = await client.get_user_by_id('44196397')
    print(user)


    user_tweets = await client.get_user_tweets('44196397')
    print(user_tweets)

    tweet = await client.get_tweet_by_id('1519480761749016577')
    print(tweet)

asyncio.run(main())
