import asyncio
from twikit import Client

async def main():
    client = Client()
    
    # Load your saved cookies if you have them
    client.load_cookies('path/to/cookies.json')
    
    # Or login directly
    # await client.login(auth_info_1='...', auth_info_2='...', password='...')
    
    # Get a tweet and check its bookmark count
    tweet = await client.get_tweet_by_id('1519480761749016577')
    print(f"Tweet bookmark count: {tweet.bookmark_count}")

if __name__ == "__main__":
    asyncio.run(main()) 