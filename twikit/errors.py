class TwitterException(Exception):
    """
    Base class for Twitter API related exceptions.
    """

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

ERROR_CODE_TO_EXCEPTION: dict[int, TwitterException] = {
    187: DuplicateTweet,
}


def raise_exceptions_from_response(errors: list[dict]):
    for error in errors:
        code = error.get('code')
        if code not in ERROR_CODE_TO_EXCEPTION:
            code = error.get('extensions', {}).get('code')
        exception = ERROR_CODE_TO_EXCEPTION[code]
        if exception is not None:
            raise exception(error['message'])
