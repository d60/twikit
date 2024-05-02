import httpx

from ..errors import (
    TwitterError,
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    RequestTimeoutError,
    TooManyRequestsError,
    ServerError,
)


class HTTPClient:
    def __init__(self, **kwargs) -> None:
        self.client = httpx.AsyncClient(**kwargs)

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        response = await self.client.request(method, url, **kwargs)
        status_code = response.status_code
        self._remove_duplicate_ct0_cookie()

        if status_code >= 400:
            message = f'status: {status_code}, message: "{response.text}"'
            if status_code == 400:
                raise BadRequestError(message, headers=response.headers)
            elif status_code == 401:
                raise UnauthorizedError(message, headers=response.headers)
            elif status_code == 403:
                raise ForbiddenError(message, headers=response.headers)
            elif status_code == 404:
                raise NotFoundError(message, headers=response.headers)
            elif status_code == 408:
                raise RequestTimeoutError(message, headers=response.headers)
            elif status_code == 429:
                raise TooManyRequestsError(message, headers=response.headers)
            elif 500 <= status_code < 600:
                raise ServerError(message, headers=response.headers)
            else:
                raise TwitterError(message, headers=response.headers)

        return response

    async def get(self, url, **kwargs) -> httpx.Response:
        return await self.request('GET', url, **kwargs)

    async def post(self, url, **kwargs) -> httpx.Response:
        return await self.request('POST', url, **kwargs)

    def _remove_duplicate_ct0_cookie(self) -> None:
        cookies = {}
        for cookie in self.client.cookies.jar:
            if 'ct0' in cookies and cookie.name == 'ct0':
                continue
            cookies[cookie.name] = cookie.value
        self.client.cookies = list(cookies.items())
