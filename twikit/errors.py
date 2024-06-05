from __future__ import annotations


class TwitterException(Exception):
    """
    Base class for Twitter API related exceptions.
    """
    def __init__(self, *args: object, headers: dict | None = None) -> None:
        super().__init__(*args)
        if headers is None:
            self.headers = None
        else:
            self.headers = dict(headers)

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
    def __init__(self, *args, headers: dict | None = None) -> None:
        super().__init__(*args, headers=headers)
        if headers is not None and 'x-rate-limit-reset' in headers:
            self.rate_limit_reset = int(headers.get('x-rate-limit-reset'))
        else:
            self.rate_limit_reset = None

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
    Exception raised when a user does not exsit.
    """

class UserUnavailable(TwitterException):
    """
    Exception raised when a user is unavailable.
    """

class AccountSuspended(TwitterException):
    """
    Exception raised when the account is suspended.
    """

class AccountLocked(TwitterException):
    """
    Exception raised when the account is locked (very likey is Arkose challenge).
    """

ERROR_CODE_TO_EXCEPTION: dict[int, TwitterException] = {
    187: DuplicateTweet,
    324: InvalidMedia
}


def raise_exceptions_from_response(errors: list[dict]):
    for error in errors:
        code = error.get('code')
        if code not in ERROR_CODE_TO_EXCEPTION:
            code = error.get('extensions', {}).get('code')
        exception = ERROR_CODE_TO_EXCEPTION.get(code)
        if exception is not None:
            raise exception(error['message'])
