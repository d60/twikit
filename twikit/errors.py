from typing import List, Dict, Optional
from collections import defaultdict


class TwitterException(Exception):
    """
    Base class for Twitter API related exceptions.
    """
    def __init__(self, error: dict = None, **kwargs) -> None:
        self.error = error or {}
        self.message = error.get('message', '')

        super().__init__(self.message, **kwargs)

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
    pass

class DuplicateTweet(CouldNotTweet):
    """
    Exception raised when a tweet is a duplicate of another.
    """
    pass


ERROR_CODE_TO_EXCEPTION: Dict[int, Optional[TwitterException]] = defaultdict(lambda: None, {
    187: DuplicateTweet,
})


def raise_exceptions_from_response(error_list: List[dict]):
    """
    This works assuming that the error codes are in:
    - error['code']
    - error['extensions']['code']

    this is an example of one error (returned on a duplicate tweet error):
    {
            'message': 'Authorization: Status is a duplicate. (187)', 
            'locations': [{'line': 18, 'column': 3}], 
            'path': ['create_tweet'], 
            'extensions': {
                'name': 'AuthorizationError', 
                'source': 'Client', 
                'code': 187, 
                'kind': 'Permissions', 
                'tracing': {'trace_id': '...'}
            }, 
            'code': 187, 
            'kind': 'Permissions', 
            'name': 'AuthorizationError', 
            'source': 'Client', 
            'tracing': {'trace_id': '...'}
        }
    """
    global ERROR_CODE_TO_EXCEPTION
    
    for error in error_list:
        # getting the error code from either ['code'] or []'extensions']['code']
        code = error.get('code')
        if code not in ERROR_CODE_TO_EXCEPTION:
            code = error.get('extensions', {}).get('code')
        
        exception = ERROR_CODE_TO_EXCEPTION[code]
        
        if exception is not None:
            raise exception(error)
