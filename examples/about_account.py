import asyncio
from twikit.guest import Client


AUTH_INFO_1 = '...'
AUTH_INFO_2 = '...'
PASSWORD = '...'

client = Client('en-US')


async def main():
    client.load_cookies('cookies.json')
    client_user = await client.user()

    about = await client.get_user_about('sama')
    print(about)
    print(f'Based in: {about.account_based_in}')
    print(f'Username changes: {about.username_changes}')
    print(f'Identity verified: {about.is_identity_verified}')


if __name__ == '__main__':
    asyncio.run(main())
