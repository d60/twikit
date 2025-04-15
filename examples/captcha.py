import asyncio

from twikit import Client,TwoCaptcher

###########################################

# Enter your account information,proxy,2captcha token
USERNAME = ...
EMAIL = ...
PASSWORD = ...
PROXY = ...
API_KEY = ...



async def main():
    captcha_solver = TwoCaptcher(api_key=API_KEY)


    client = Client(captcha_solver=captcha_solver,proxy=PROXY)

    # Asynchronous client methods are coroutines and
    # must be called using `await`.
    await client.login(
        auth_info_1=USERNAME,
        auth_info_2=EMAIL,
        password=PASSWORD
        
    )



asyncio.run(main())
