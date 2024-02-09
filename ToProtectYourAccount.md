# What you need to do to protect your account
Since this library uses an unofficial API, your account may be banned if you use it incorrectly. Therefore, please be sure to follow the measures below.

## Avoid sending too many requests
Sending too many requests may be perceived as suspicious behavior. Therefore, please avoid sending consecutive requests and allow time for a cooldown. Specifically, you should not send so many requests that you get stuck in a [rate limit](https://github.com/d60/twikit/blob/main/ratelimits.md).

## Reuse login information
As mentioned earlier, sending many requests can be perceived as suspicious behavior, especially logins, which are closely monitored. Therefore, the act of repeatedly calling the `login` method should be avoided. To do so, it is useful to reuse the login information contained in cookies by using the `save_cookies` and `load_cookies` methods. The specific methods are shown below:

The first time, there is a way to log in using the `login` method.
```python
client.login(
    auth_info_1='...',
    auth_info_2='...',
    password='...'
)
```
Then save the cookies.
```python
client.save_cookies('cookies.json')
```
After the second time, load the saved cookies.
```python
client.load_cookies('cookies.json')
```

## Don't tweet sensitive content.
You should not tweet sensitive content, especially content related to sexuality, violence, politics, discrimination, or hate speech. This is because such content violates Twitter's terms and conditions and may be banned.

#
**Please use Twikit safely in accordance with the above instructions!**
