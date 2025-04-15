from __future__ import annotations

from time import sleep

from typing import Optional

import httpx

from .base import CaptchaSolver


class TwoCaptcher(CaptchaSolver):
    """
    You can automatically unlock the account by passing the `captcha_solver`
    argument when initialising the :class:`.Client`.

    First, visit https://2captcha.com and obtain your 2Captcha API key.
    Next, pass the 2Captcha instance to the client as shown in the example.

    .. code-block:: python

        from twikit.twikit_async import TwoCaptcher, Client
        solver = TwoCaptcher(
            api_key='your_api_key',
            max_attempts=10
        )
        client = Client(captcha_solver=solver)

    Parameters
    ----------
    api_key : :class:`str`
        2Captcha API key.
    max_attempts : :class:`int`, default=3
        The maximum number of attempts to solve the captcha.
    get_result_interval : :class:`float`, default=1.0

    use_blob_data : :class:`bool`, default=False
    """

    def __init__(
        self,
        api_key: str,
        max_attempts: int = 3,
        get_result_interval: float = 1.0,
        use_blob_data: bool = False
    ) -> None:
        self.api_key = api_key
        self.get_result_interval = get_result_interval
        self.max_attempts = max_attempts
        self.use_blob_data = use_blob_data

    def create_task(self, task_data: dict) -> dict:
        data = {
            'clientKey': self.api_key,
            'task': task_data
        }
        response = httpx.post(
            'https://api.2captcha.com/createTask',
            json=data,
            headers={'content-type': 'application/json'}
        ).json()
        return response

    def get_task_result(self, task_id: str) -> dict:
        data = {
            'clientKey': self.api_key,
            'taskId': task_id
        }
        response = httpx.post(
            'https://api.2captcha.com/getTaskResult',
            json=data,
            headers={'content-type': 'application/json'}
        ).json()
        return response

    def solve_funcaptcha(self, blob: Optional[str] = None, websiteURL: Optional[str] = None, siteKey: Optional[str] = None) -> dict:
        task_data = {
            'type': 'FunCaptchaTaskProxyless',
            'websiteURL': websiteURL if websiteURL else 'https://iframe.arkoselabs.com',
            'websitePublicKey': siteKey if siteKey else self.CAPTCHA_SITE_KEY,
            'funcaptchaApiJSSubdomain': 'https://client-api.arkoselabs.com',
        }

        if self.use_blob_data:
            task_data['data'] = '{"blob":"%s"}' % blob
            task_data['userAgent'] = self.client._user_agent
        task = self.create_task(task_data)
        while True:
            sleep(self.get_result_interval)
            result = self.get_task_result(task['taskId'])
            if result.get('status') in ('ready', 'failed'):
                return result
            if result.get('errorCode'):
                return result
