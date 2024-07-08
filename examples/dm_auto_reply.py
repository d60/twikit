import asyncio
import os

from twikit import Client
from twikit.streaming import Topic

AUTH_INFO_1 = ''
AUTH_INFO_2 = ''
PASSWORD = ''

client = Client()


async def main():
    if os.path.exists('cookies.json'):
        client.load_cookies('cookies.json')
    else:
        await client.login(
            auth_info_1=AUTH_INFO_1,
            auth_info_2=AUTH_INFO_2,
            password=PASSWORD
        )
        client.save_cookies('cookies.json')


    user_id = '1752362966203469824'  # User ID of the DM partner to stream.
    reply_message = 'Hello'

    topics = {
        Topic.dm_update(f'{client.user_id()}-{user_id}')
    }
    streaming_session = await client.get_streaming_session(topics)

    async for topic, payload in streaming_session:
        if payload.dm_update:
            if client.user_id() == payload.dm_update.user_id:
                continue
            await client.send_dm(payload.dm_update.user_id, reply_message)

asyncio.run(main())

