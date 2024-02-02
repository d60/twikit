"""
==========================
Twikit Twitter API Wrapper
==========================

A Python library for interacting with the Twitter API.
"""

import asyncio
import os

if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from .client import Client
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
from .tweet import Tweet
from .user import User

__version__ = '1.1.0'
