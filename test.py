from twikit import Client

AUTH_INFO_1 = 'kaweco2@outlook.jp'
AUTH_INFO_2 = 'JamLoopso'
PASSWORD = 'kaweco2kaweco'

client = Client('en-US')

# client.login(
#     auth_info_1=AUTH_INFO_1,
#     auth_info_2=AUTH_INFO_2,
#     password=PASSWORD
# )
# client.save_cookies('cookies.pkl')
client.load_cookies('cookies.pkl')

client.unfollow_user('184004752')
import json

def log(obj, path = 'log.json'):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=4, ensure_ascii=False)