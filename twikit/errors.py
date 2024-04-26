from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from httpx import Headers


class TwitterError(Exception):
    """
    Base class for Twitter API related exceptions.
    """

    def __init__(self, *args: object, headers: Headers | None = None) -> None:
        super().__init__(*args)
        self.headers = None if headers is None else dict(headers)


class BadRequestError(TwitterError):
    """
    Exception raised for 400 Bad Request errors.
    """


class UnauthorizedError(TwitterError):
    """
    Exception raised for 401 Unauthorized errors.
    """


class ForbiddenError(TwitterError):
    """
    Exception raised for 403 Forbidden errors.
    """


class NotFoundError(TwitterError):
    """
    Exception raised for 404 Not Found errors.
    """


class RequestTimeoutError(TwitterError):
    """
    Exception raised for 408 Request Timeout errors.
    """


class TooManyRequestsError(TwitterError):
    """
    Exception raised for 429 Too Many Requests errors.
    """

    def __init__(self, *args: Any, headers: Headers | None = None) -> None:
        super().__init__(*args, headers=headers)
        self.rate_limit_reset: int | None
        if headers is not None and 'x-rate-limit-reset' in headers:
            self.rate_limit_reset = int(headers.get('x-rate-limit-reset'))


class ServerError(TwitterError):
    """
    Exception raised for 5xx Server Error responses.
    """


class CouldNotTweetError(TwitterError):
    """
    Exception raised when a tweet could not be sent.
    """


class DuplicateTweetError(CouldNotTweetError):
    """
    Exception raised when a tweet is a duplicate of another.
    """


class TweetNotAvailableError(TwitterError):
    """
    Exceptions raised when a tweet is not available.
    """


class InvalidMediaError(TwitterError):
    """
    Exception raised when there is a problem with the media ID
    sent with the tweet.
    """


class UserNotFoundError(TwitterError):
    """
    Exception raised when a user does not exist.
    """


class UserUnavailableError(TwitterError):
    """
    Exception raised when a user is not available.
    """


ERROR_CODE_TO_EXCEPTION: dict[int, type[TwitterError]] = {
    187: DuplicateTweetError,
    324: InvalidMediaError,
}


def raise_exceptions_from_response(errors: list[dict]):
    for error in errors:
        code = error.get('code', error.get('extensions', {}).get('code'))
        if exception := ERROR_CODE_TO_EXCEPTION.get(code):
            raise exception(error['message'])
