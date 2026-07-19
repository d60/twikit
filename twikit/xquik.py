"""Optional Xquik client for authenticated public X search."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional

import httpx

VALID_QUERY_TYPES = {"Latest", "Top"}
MAX_SEARCH_LIMIT = 200


@dataclass(frozen=True)
class XquikTweet:
    """A normalized tweet returned by an Xquik search."""

    id: str
    text: str
    created_at: Optional[str]
    author_username: Optional[str]
    author_name: Optional[str]
    reply_count: int
    retweet_count: int
    quote_count: int
    favorite_count: int
    raw: Mapping[str, Any]

    @classmethod
    def from_api(cls, tweet: Mapping[str, Any]) -> "XquikTweet":
        """Create a normalized tweet from an Xquik response object."""

        author = tweet.get("author")
        author_data = author if isinstance(author, Mapping) else {}
        return cls(
            id=str(tweet.get("id", "")),
            text=str(tweet.get("text", "")),
            created_at=_optional_string(tweet.get("createdAt")),
            author_username=_optional_string(author_data.get("username")),
            author_name=_optional_string(author_data.get("name")),
            reply_count=_int_value(tweet.get("replyCount")),
            retweet_count=_int_value(tweet.get("retweetCount")),
            quote_count=_int_value(tweet.get("quoteCount")),
            favorite_count=_int_value(tweet.get("likeCount")),
            raw=tweet,
        )


@dataclass(frozen=True)
class XquikSearchResult:
    """A page of normalized tweets and its pagination metadata."""

    tweets: List[XquikTweet]
    has_next_page: bool
    next_cursor: Optional[str]
    raw: Mapping[str, Any]


class XquikSearchClient:
    """Search public X data through the documented Xquik REST endpoint."""

    DEFAULT_BASE_URL = "https://xquik.com"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 10.0,
        client: Optional[httpx.Client] = None,
    ) -> None:
        """Configure the search client and resolve its API key."""

        self.api_key = api_key or os.environ.get("XQUIK_API_KEY")
        if not self.api_key:
            raise ValueError("Set api_key or XQUIK_API_KEY before searching with Xquik.")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = client

    def search(
        self,
        query: str,
        query_type: str = "Latest",
        limit: int = 20,
        cursor: Optional[str] = None,
        since_time: Optional[str] = None,
        until_time: Optional[str] = None,
    ) -> XquikSearchResult:
        """Search tweets and return normalized results."""

        self._validate_search(query, query_type, limit, since_time, until_time)
        params: Dict[str, Any] = {
            "q": query,
            "queryType": query_type,
            "limit": limit,
        }
        if cursor:
            params["cursor"] = cursor
        if since_time:
            params["sinceTime"] = since_time
        if until_time:
            params["untilTime"] = until_time

        data = self._get_search(params)
        raw_tweets = data.get("tweets", [])
        tweets = [
            XquikTweet.from_api(tweet)
            for tweet in raw_tweets
            if isinstance(tweet, Mapping)
        ]
        return XquikSearchResult(
            tweets=tweets,
            has_next_page=bool(data.get("has_next_page")),
            next_cursor=_optional_string(data.get("next_cursor")),
            raw=data,
        )

    def _get_search(self, params: Mapping[str, Any]) -> Mapping[str, Any]:
        """Execute one search request and validate its response shape."""

        owned_client = self.client is None
        client = self.client or httpx.Client(timeout=self.timeout)
        try:
            response = client.get(
                f"{self.base_url}/api/v1/x/tweets/search",
                headers={"x-api-key": self.api_key},
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, Mapping):
                raise ValueError("Xquik search response must be a JSON object.")
            return data
        finally:
            if owned_client:
                client.close()

    def _validate_search(
        self,
        query: str,
        query_type: str,
        limit: int,
        since_time: Optional[str],
        until_time: Optional[str],
    ) -> None:
        """Validate search parameters before sending a request."""

        if not query:
            raise ValueError("query is required.")
        if query_type not in VALID_QUERY_TYPES:
            allowed = ", ".join(sorted(VALID_QUERY_TYPES))
            raise ValueError(f"query_type must be one of: {allowed}.")
        if not isinstance(limit, int) or isinstance(limit, bool):
            raise ValueError("limit must be an integer.")
        if not 1 <= limit <= MAX_SEARCH_LIMIT:
            raise ValueError(f"limit must be between 1 and {MAX_SEARCH_LIMIT}.")
        _validate_iso_time(since_time, "since_time")
        _validate_iso_time(until_time, "until_time")


def _optional_string(value: Any) -> Optional[str]:
    """Convert a present value to text while preserving missing values."""

    return str(value) if value is not None else None


def _int_value(value: Any) -> int:
    """Normalize integer-like response values without raising."""

    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip().replace(",", ""))
        except ValueError:
            return 0
    return 0


def _validate_iso_time(value: Optional[str], name: str) -> None:
    """Validate an optional ISO 8601 timestamp."""

    if value is None:
        return
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be an ISO 8601 string.")
    normalized = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO 8601 string.") from exc
