from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from httpx import Headers


class TwitterException(Exception):
    """
    Base class for Twitter API related exceptions.
    """

    def __init__(self, *args: object, headers: Headers | None = None) -> None:
        super().__init__(*args)
        self.headers = None if headers is None else dict(headers)


class BadRequest(TwitterException):
    """
    Exception raised for 400 Bad Request errors.
    """


class Unauthorized(TwitterException):
    """
    Exception raised for 401 Unauthorized errors.
    """


class Forbidden(TwitterException):
    """
    Exception raised for 403 Forbidden errors.
    """


class NotFound(TwitterException):
    """
    Exception raised for 404 Not Found errors.
    """


class RequestTimeout(TwitterException):
    """
    Exception raised for 408 Request Timeout errors.
    """


class TooManyRequests(TwitterException):
    """
    Exception raised for 429 Too Many Requests errors.
    """

    def __init__(self, *args, headers: Headers | None = None) -> None:
        super().__init__(*args, headers=headers)
        self.rate_limit_reset: int | None
        if headers is not None and 'x-rate-limit-reset' in headers:
            self.rate_limit_reset = int(headers.get('x-rate-limit-reset'))


class ServerError(TwitterException):
    """
    Exception raised for 5xx Server Error responses.
    """


class CouldNotTweet(TwitterException):
    """
    Exception raised when a tweet could not be sent.
    """


class DuplicateTweet(CouldNotTweet):
    """
    Exception raised when a tweet is a duplicate of another.
    """


class TweetNotAvailable(TwitterException):
    """
    Exceptions raised when a tweet is not available.
    """


class InvalidMedia(TwitterException):
    """
    Exception raised when there is a problem with the media ID
    sent with the tweet.
    """


class UserNotFound(TwitterException):
    """
    Exception raised when a user does not exist.
    """


class UserUnavailable(TwitterException):
    """
    Exception raised when a user is not available.
    """


ERROR_CODE_TO_EXCEPTION: dict[int, type[TwitterException]] = {
    187: DuplicateTweet,
    324: InvalidMedia,
}


def raise_exceptions_from_response(errors: list[dict]):
    for error in errors:
        code = error.get('code', error.get('extensions', {}).get('code'))
        if exception := ERROR_CODE_TO_EXCEPTION.get(code):
            raise exception(error['message'])
