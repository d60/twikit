"""
==========================
Twikit Twitter API Wrapper
==========================

https://github.com/d60/twikit
A Python library for interacting with the Twitter API.
"""

__version__ = '2.3.3'

import asyncio
import os

if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from ._captcha import Capsolver
from .bookmark import BookmarkFolder
from .errors import *
from .utils import build_query
from .client.client import Client
from .community import Community, CommunityCreator, CommunityMember, CommunityRule
from .geo import Place
from .group import Group, GroupMessage
from .list import List
from .message import Message
from .notification import Notification
from .trend import Trend
from .tweet import CommunityNote, Poll, ScheduledTweet, Tweet
from .user import User
