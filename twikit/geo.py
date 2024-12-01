from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

from .errors import TwitterException

if TYPE_CHECKING:
    from .client.client import Client


class Place:
    """
    Attributes
    ----------
    id : :class:`str`
        The ID of the place.
    name : :class:`str`
        The name of the place.
    full_name : :class:`str`
        The full name of the place.
    country : :class:`str`
        The country where the place is located.
    country_code : :class:`str`
        The ISO 3166-1 alpha-2 country code of the place.
    url : :class:`str`
        The URL providing more information about the place.
    place_type : :class:`str`
        The type of place.
    attributes : :class:`dict`
    bounding_box : :class:`dict`
        The bounding box that defines the geographical area of the place.
    centroid : list[:class:`float`] | None
        The geographical center of the place, represented by latitude and
        longitude.
    contained_within : list[:class:`.Place`]
        A list of places that contain this place.
    """

    def __init__(self, client: Client, data: dict) -> None:
        self._client = client

        self.id: str = data['id']
        self.name: str = data['name']
        self.full_name: str = data['full_name']
        self.country: str = data['country']
        self.country_code: str = data['country_code']
        self.url: str = data['url']
        self.place_type: str = data['place_type']
        self.attributes: dict | None = data.get('attributes')
        self.bounding_box: dict = data['bounding_box']
        self.centroid: list[float] | None = data.get('centroid')

        self.contained_within: list[Place] = [
            Place(client, place) for place in data.get('contained_within', [])
        ]

    async def update(self) -> None:
        new = self._client.get_place(self.id)
        await self.__dict__.update(new.__dict__)

    def __repr__(self) -> str:
        return f'<Place id="{self.id}" name="{self.name}">'

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, Place) and self.id == __value.id

    def __ne__(self, __value: object) -> bool:
        return not self == __value


def _places_from_response(client: Client, response: dict) -> list[Place]:
    if 'errors' in response:
        e = response['errors'][0]
        # No data available for the given coordinate.
        if e['code'] == 6:
            warnings.warn(e['message'])
        else:
            raise TwitterException(e['message'])

    places = response['result']['places'] if 'result' in response else []
    return [Place(client, place) for place in places]
