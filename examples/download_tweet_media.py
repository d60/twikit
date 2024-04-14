import asyncio
import time

from twikit.twikit_async import Client

AUTH_INFO_1 = '...'
AUTH_INFO_2 = '...'
PASSWORD = '...'

client = Client('en-US')


tweet = client.get_tweet_by_id('...')

for i, media in enumerate(tweet.media):
    media_url = media.get('media_url_https')
    extension = media_url.rsplit('.', 1)[-1]

    response = client.get_media(media_url)

    with open(f'media_{i}.{extension}', 'wb') as f:
        f.write(response.content)
