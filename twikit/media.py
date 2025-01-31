from __future__ import annotations

from typing import TYPE_CHECKING

import m3u8
import webvtt
from m3u8 import M3U8

if TYPE_CHECKING:
    from .client.client import Client


class Media:
    """
    A base class representing media object.

    Attributes
    ----------
    id : :class:`str`
        The media ID.
    display_url : :class:`str`
        The display URL.
    expanded_url : :class:`str`
        The expanded display URL.
    media_url : :class:`str`
        The media URL.
    source_status_id : :class:`str`
        The source tweet ID.
    source_user_id : :class:`str`
        The ID of the user who posted the source tweet.
    type : :class:`str`
        The media type.
    url : :class:`str`
        The URL of the media.
    sizes : :class:`dict`
        The sizes of the media.
    original_info : :class:`str`
    width : :class:`int`
        The width of the media.
    height : :class:`int`
        The height of the media.
    focus_rects : :class:`list`
    """
    def __init__(self, client: Client, data: dict) -> None:
        self._client = client
        self._data = data

    @property
    def id(self) -> str:
        return self._data.get('id_str')

    @property
    def display_url(self) -> str:
        return self._data.get('display_url')

    @property
    def expanded_url(self) -> str:
        return self._data.get('expanded_url')

    @property
    def media_url(self) -> str:
        return self._data.get('media_url_https')

    @property
    def source_status_id(self) -> str:
        return self._data.get('source_status_id_str')

    @property
    def source_user_id(self) -> str:
        return self._data.get('source_user_id_str')

    @property
    def type(self) -> str:
        return self._data.get('type')

    @property
    def url(self) -> str:
        return self._data.get('url')

    # Add source user
    @property
    def sizes(self) -> dict:
        return self._data.get('sizes')

    @property
    def original_info(self) -> str:
        return self._data.get('original_info')

    @property
    def width(self) -> int:
        return self.original_info.get('width')

    @property
    def height(self) -> int:
        return self.original_info.get('height')

    @property
    def focus_rects(self) -> list:
        return self.original_info.get('focus_rects')

    async def get(self) -> bytes:
        response = await self._client.http.get(self.media_url)
        return response.content

    async def download(self, output_path: str) -> None:
        with open(output_path, 'wb') as f:
            f.write(await self.get())

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id}>'


class Photo(Media):
    """
    A class representing a photo media object.

    Attributes
    ----------
    features : :class:`dict`
        The features of the photo.
    """
    @property
    def features(self) -> dict:
        return self._data.get('features')


class Stream:
    """
    The Stream class represents a media stream

    Attributes
    ----------
    url : :class:`str`
        The url of the stream.
    bitrate : :class:`int`
        The bitrate of the stream.
    content_type : :class:`str`
        The mimetype of the stream content.
    """
    def __init__(self, client: Client, data: dict) -> None:
        self._client = client
        self._data = data

    @property
    def url(self) -> str:
        return self._data.get('url')

    @property
    def bitrate(self) -> int:
        return self._data.get('bitrate')

    @property
    def content_type(self) -> str:
        return self._data.get('content-type')

    async def get(self) -> bytes:
        """
        Retrieves the stream content.

        Returns
        -------
        :class:`bytes`
            The raw content of the stream.
        """
        response = await self._client.http.get(self.url)
        return response.content

    async def download(self, output_path: str) -> None:
        """
        Downloads the stream content and saves it to the specified file.

        Parameters
        ----------
        output_path : :class:`str`
            The path where the downloaded file will be saved.
        """
        with open(output_path, 'wb') as f:
            f.write(await self.get())

    def __repr__(self) -> str:
        return f'<Stream url="{self.url}">'


class AnimatedGif(Media):
    """
    A class representing an animated GIF media object.

    Attributes
    ----------
    video_info : :class:`dict`
        The video information of the GIF.
    aspect_ratio : :class:`tuple[int, int]`
        The aspect ratio of the GIF.
    streams : list[:class:`Stream`]
        The list of video streams for the GIF.
    """
    @property
    def video_info(self) -> dict:
        return self._data.get('video_info')

    @property
    def aspect_ratio(self) -> tuple[int, int]:
        return tuple(self.video_info['aspect_ratio'])

    @property
    def streams(self) -> list:
        return [Stream(self._client, stream_data) for stream_data in self.video_info.get('variants')]


class Video(Media):
    """
    A class representing a video media object.


    .. code-block:: python

        # Video download example
        tweet = await client.get_tweet_by_id('00000000000')
        video = tweet.media[0]
        streams = video.streams
        await streams[0].download('output.mp4')

    Attributes
    ----------
    video_info : :class:`dict`
        The video information.
    aspect_ratio : :class:`tuple[int, int]`
        The aspect ratio of the video.
    duration_millis : :class:`int`
        The duration of the video in milliseconds.
    streams : list[:class:`Stream`]
        The list of video streams for the video.
    """
    def __init__(self, client: Client, data: dict) -> None:
        super().__init__(client, data)
        self._playlist: M3U8 | None = None
        self._subtitles_playlist: M3U8 | None = None
        self._base_url = 'https://video.twimg.com'

    @property
    def video_info(self) -> dict:
        return self._data.get('video_info')

    @property
    def aspect_ratio(self) -> tuple[int, int]:
        return tuple(self.video_info['aspect_ratio'])

    @property
    def duration_millis(self) -> int:
        return self.video_info.get('duration_millis')

    @property
    def _streams(self) -> list:
        return self.video_info.get('variants')

    @property
    def streams(self) -> list[Stream]:
        video_streams = filter(
            lambda x: x['content_type'].startswith('video'),
            self._streams
        )
        return [Stream(self._client, stream_data) for stream_data in video_streams]

    async def _get_playlist(self) -> M3U8 | None:
        # Returns M3U8 object includes stream information.
        if self._playlist:
            return self._playlist
        m3u8_stream = next(
            filter(
                lambda x: x['content_type'] == 'application/x-mpegURL',
                self._streams
            ),
            None
        )
        if not m3u8_stream:
            raise None
        response, _ = await self._client.get(m3u8_stream['url'])
        playlist = m3u8.loads(response)
        self._playlist = playlist
        return playlist

    async def _get_subtitles_playlist(self) -> M3U8 | None:
        # Returns M3U8 object includes subtitles information.
        if self._subtitles_playlist:
            return self._subtitles_playlist
        playlist = await self._get_playlist()
        if not playlist:
            return None
        subtitles_media = next(
            filter(
                lambda x: x.type == 'SUBTITLES',
                playlist.media
            ),
            None
        )
        if not subtitles_media:
            return None
        response, _ = await self._client.get(self._base_url + subtitles_media.uri)
        playlist = m3u8.loads(response)
        self._subtitles_playlist = playlist
        return playlist

    async def get_subtitles(self) -> webvtt.WebVTT | None:
        """
        Retrieves the subtitles for the video.

        Returns
        -------
        :class:`webvtt.WebVTT` | None
            Returns the subtitles for the video. If the video does not have subtitles, returns None.
            Refer https://github.com/glut23/webvtt-py for more information.

        Examples
        --------
        .. code-block:: python

            tweet = await client.get_tweet_by_id('00000000000')
            video = tweet.media[0]
            subtitles = await video.get_subtitles()
            for l in subtitles:
                print(l.start)
                print(l.end)
                print(l.text)
        """
        subtitles_playlist = await self._get_subtitles_playlist()
        if not subtitles_playlist:
            return None
        response, _ = await self._client.get(self._base_url + subtitles_playlist.segments[0].uri)
        return webvtt.from_string(response)


MEDIA_TYPE = Video | Photo | AnimatedGif
MEDIA_TYPE_MAPPING = {
    'video': Video,
    'photo': Photo,
    'animated_gif': AnimatedGif
}


def _media_from_data(client, data) -> Media:
    type = data['type']
    cls = MEDIA_TYPE_MAPPING.get(type)
    if not cls:
        print('unknown media type')
        return
    return cls(client, data)
