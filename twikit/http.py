import httpx

from .errors import (
    TwitterException,
    BadRequest,
    Unauthorized,
    Forbidden,
    NotFound,
    RequestTimeout,
    TooManyRequests,
    ServerError
)


class HTTPClient:
    def __init__(self, **kwargs) -> None:
        self.client = httpx.Client(**kwargs)

    def request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        response = self.client.request(method, url, **kwargs)
        status_code = response.status_code
        self._remove_duplicate_ct0_cookie()

        if status_code >= 400:
            message = f'status: {status_code}, message: "{response.text}"'
            if status_code == 400:
                raise BadRequest(message)
            elif status_code == 401:
                raise Unauthorized(message)
            elif status_code == 403:
                raise Forbidden(message)
            elif status_code == 404:
                raise NotFound(message)
            elif status_code == 408:
                raise RequestTimeout(message)
            elif status_code == 429:
                raise TooManyRequests(message)
            elif 500 <= status_code < 600:
                raise ServerError(message)
            else:
                raise TwitterException(message)

        return response

    def get(self, url, **kwargs) -> httpx.Response:
        return self.request('GET', url, **kwargs)

    def post(self, url, **kwargs) -> httpx.Response:
        return self.request('POST', url, **kwargs)

    def _remove_duplicate_ct0_cookie(self) -> None:
        cookies = {}
        for cookie in self.client.cookies.jar:
            if 'ct0' in cookies and cookie.name == 'ct0':
                continue
            cookies[cookie.name] = cookie.value
        self.client.cookies = list(cookies.items())
