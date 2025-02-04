import asyncio
from twikit import Client

AUTH_INFO_1 = '...'
AUTH_INFO_2 = '...'
PASSWORD = '...'

client = Client('en-US')


async def main():
    tweet = await client.get_tweet_by_id('...')

    for i, media in enumerate(tweet.media):
        if media.type == 'photo':
            await media.download(f'media_{i}.jpg')
        if media.type == 'animated_gif':
            await media.streams[-1].download(f'media_{i}.mp4')
        if media.type == 'video':
            await media.streams[-1].download(f'media_{i}.mp4')

asyncio.run(main())
