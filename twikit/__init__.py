"""
==========================
Twikit Twitter API Wrapper
==========================

A Python library for interacting with the Twitter API.
"""

__version__ = '1.5.8'

from .bookmark import BookmarkFolder
from .client import Client
from .community import Community, CommunityCreator, CommunityMember, CommunityRule
from .errors import (
    BadRequestError,
    CouldNotTweetError,
    DuplicateTweetError,
    ForbiddenError,
    InvalidMediaError,
    NotFoundError,
    RequestTimeoutError,
    ServerError,
    TooManyRequestsError,
    TweetNotAvailableError,
    TwitterError,
    UnauthorizedError,
    UserNotFoundError,
    UserUnavailableError,
)
from .group import Group, GroupMessage
from .list import List
from .message import Message
from .notification import Notification
from .trend import Trend
from .tweet import CommunityNote, Poll, ScheduledTweet, Tweet
from .user import User
from .utils import build_query

__all__ = [
    'BookmarkFolder',
    'Client',
    'Community',
    'CommunityCreator',
    'CommunityMember',
    'CommunityRule',
    'Group',
    'GroupMessage',
    'List',
    'Message',
    'Notification',
    'Trend',
    'CommunityNote',
    'Poll',
    'ScheduledTweet',
    'Tweet',
    'User',
    'build_query',
    'TwitterError',
    'BadRequestError',
    'UnauthorizedError',
    'ForbiddenError',
    'NotFoundError',
    'RequestTimeoutError',
    'TooManyRequestsError',
    'ServerError',
    'CouldNotTweetError',
    'DuplicateTweetError',
    'TweetNotAvailableError',
    'InvalidMediaError',
    'UserNotFoundError',
    'UserUnavailableError',
]
