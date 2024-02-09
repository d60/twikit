from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Client


class Trend:
    """
    Attributes
    ----------
    name : str
        The name of the trending topic.
    tweets_count : int
        The count of tweets associated with the trend.
    domain_context : str
        The context or domain associated with the trend.
    grouped_trends : list[str]
        A list of trend names grouped under the main trend.
    """

    def __init__(self, client: Client, data: dict) -> None:
        self._client = client

        metadata: dict = data['trendMetadata']
        self.name: str = data['name']
        self.tweets_count: int | None = metadata.get('metaDescription')
        self.domain_context: str = metadata.get('domainContext')
        self.grouped_trends: list[str] = [
            trend['name'] for trend in data.get('groupedTrends', [])
        ]

    def __repr__(self) -> str:
        return f'<Trend name="{self.name}">'
