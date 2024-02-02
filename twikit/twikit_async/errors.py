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
