import asyncio
from twikit import Client

AUTH_INFO_1 = '...'
AUTH_INFO_2 = '...'
PASSWORD = '...'

client = Client('en-US')


async def main():
    tweet = await client.get_tweet_by_id('...')

    for i, media in enumerate(tweet.media):
        media_url = media.get('media_url_https')
        extension = media_url.rsplit('.', 1)[-1]

        response = await client.get(media_url, headers=client._base_headers)

        with open(f'media_{i}.{extension}', 'wb') as f:
            f.write(response.content)

asyncio.run(main())
