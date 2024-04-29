from http import HTTPStatus
from typing import Any

import httpx

from twikit.errors import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    RequestTimeoutError,
    ServerError,
    TooManyRequestsError,
    TwitterError,
    UnauthorizedError,
)


class HTTPClient:
    def __init__(self, **kwargs: Any) -> None:
        self.client = httpx.Client(**kwargs)

    def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        response = self.client.request(method, url, **kwargs)
        status_code = response.status_code
        self._remove_duplicate_ct0_cookie()

        exceptions = {
            HTTPStatus.BAD_REQUEST: BadRequestError,
            HTTPStatus.UNAUTHORIZED: UnauthorizedError,
            HTTPStatus.FORBIDDEN: ForbiddenError,
            HTTPStatus.NOT_FOUND: NotFoundError,
            HTTPStatus.REQUEST_TIMEOUT: RequestTimeoutError,
            HTTPStatus.TOO_MANY_REQUESTS: TooManyRequestsError,
        }
        if status_code >= HTTPStatus.BAD_REQUEST:
            message = f'status: {status_code}, message: "{response.text}"'
            exception_class = exceptions.get(HTTPStatus(status_code), TwitterError)
            if HTTPStatus.INTERNAL_SERVER_ERROR <= status_code < HTTPStatus.HTTP_VERSION_NOT_SUPPORTED:
                exception_class = ServerError
            raise exception_class(message, headers=response.headers)

        return response

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request('GET', url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request('POST', url, **kwargs)

    def _remove_duplicate_ct0_cookie(self) -> None:
        cookies = httpx.Cookies()
        for cookie in self.client.cookies.jar:
            if cookie.value is not None and (cookie.name != 'ct0' or 'ct0' not in cookies):
                cookies.set(cookie.name, cookie.value)
        self.client.cookies = cookies
