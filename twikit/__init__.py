"""
==========================
Twikit Twitter API Wrapper
==========================

A Python library for interacting with the Twitter API.
"""

from .client import Client
from .group import Group, GroupMessage
from .list import List
from .errors import (
    BadRequest,
    Forbidden,
    NotFound,
    RequestTimeout,
    ServerError,
    TooManyRequests,
    TwitterException,
    Unauthorized
)
from .message import Message
from .trend import Trend
from .tweet import ScheduledTweet, Tweet
from .user import User
from .utils import build_query

__version__ = '1.3.10'
