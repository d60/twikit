import requests

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
        self.client = requests.session(**kwargs)

    def request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response:
        response = self.client.request(method, url, **kwargs)
        status_code = response.status_code

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

    def get(self, url, **kwargs) -> requests.Response:
        return self.request('GET', url, **kwargs)

    def post(self, url, **kwargs) -> requests.Response:
        return self.request('POST', url, **kwargs)
