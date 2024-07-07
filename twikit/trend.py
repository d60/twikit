from __future__ import annotations

from typing import TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    from .client.client import Client


class Trend:
    """
    Attributes
    ----------
    name : :class:`str`
        The name of the trending topic.
    tweets_count : :class:`int`
        The count of tweets associated with the trend.
    domain_context : :class:`str`
        The context or domain associated with the trend.
    grouped_trends : :class:`list`[:class:`str`]
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


class PlaceTrends(TypedDict):
    trends: list[PlaceTrend]
    as_of: str
    created_at: str
    locations: dict


class PlaceTrend:
    """
    Attributes
    ----------
    name : :class:`str`
        The name of the trend.
    url : :class:`str`
        The URL to view the trend.
    query : :class:`str`
        The search query corresponding to the trend.
    tweet_volume : :class:`int`
        The volume of tweets associated with the trend.
    """
    def __init__(self, client: Client, data: dict) -> None:
        self._client = client

        self.name: str = data['name']
        self.url: str = data['url']
        self.promoted_content: None = data['promoted_content']
        self.query: str = data['query']
        self.tweet_volume: int = data['tweet_volume']

    def __repr__(self) -> str:
        return f'<PlaceTrend name="{self.name}">'


class Location:
    def __init__(self, client: Client, data: dict) -> None:
        self._client = client

        self.woeid: int = data['woeid']
        self.country: str = data['country']
        self.country_code: str = data['countryCode']
        self.name: str = data['name']
        self.parentid: int = data['parentid']
        self.placeType: dict = data['placeType']
        self.url: str = data['url']

    async def get_trends(self) -> PlaceTrends:
        return await self._client.get_place_trends(self.woeid)

    def __repr__(self) -> str:
        return f'<Location name="{self.name}" woeid={self.woeid}>'

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, Location) and self.woeid == __value.woeid

    def __ne__(self, __value: object) -> bool:
        return not self == __value