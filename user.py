from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from client import Client


class User:
    """
    Attributes
    ----------
    id (str): The unique identifier of the user.
    created_at (str): The date and time when the user account was created.
    name (str): The user's name.
    screen_name (str): The user's screen name.
    rest_id (str): The user's rest identifier.
    profile_image_url (str): The URL of the user's profile image (HTTPS version).
    profile_banner_url (str): The URL of the user's profile banner.
    url (str): The user's URL.
    location (str): The user's location information.
    description (str): The user's profile description.
    description_urls (list): URLs found in the user's profile description.
    urls (list): URLs associated with the user.
    pinned_tweet_ids (str): The IDs of tweets that the user has pinned to their profile.
    is_blue_verified (bool): Indicates if the user is verified with a blue checkmark.
    verified (bool): Indicates if the user is verified.
    possibly_sensitive (bool): Indicates if the user's content may be sensitive.
    can_dm (bool): Indicates whether the user can receive direct messages.
    can_media_tag (bool): Indicates whether the user can be tagged in media.
    want_retweets (bool): Indicates if the user wants retweets.
    default_profile (bool): Indicates if the user has the default profile.
    default_profile_image (bool): Indicates if the user has the default profile image.
    has_custom_timelines (bool): Indicates if the user has custom timelines.
    followers_count (int): The count of followers.
    fast_followers_count (int): The count of fast followers.
    normal_followers_count (int): The count of normal followers.
    following_count (int): The count of users the user is following.
    favourites_count (int): The count of favorites or likes.
    listed_count (int): The count of lists the user is a member of.
    media_count (int): The count of media items associated with the user.
    statuses_count (int): The count of tweets.
    is_translator (bool): Indicates if the user is a translator.
    translator_type (str): The type of translator.
    profile_interstitial_type (str): The type of profile interstitial.
    withheld_in_countries (list): Countries where the user's content is withheld.
    """

    def __init__(self, client: Client, data: dict):
        self._client = client

        self.id = data['id']
        self.created_at = data["legacy"]["created_at"]
        self.name = data["legacy"]["name"]
        self.screen_name = data.get('screen_name')
        self.rest_id = data['rest_id']
        self.profile_image_url = data["legacy"]["profile_image_url_https"]
        self.profile_banner_url = data["legacy"].get("profile_banner_url")
        self.url = data["legacy"].get("url")
        self.location = data["legacy"]["location"]
        self.description = data["legacy"]["description"]
        self.description_urls = data["legacy"]["entities"]["description"]["urls"]
        self.urls = data["legacy"]["entities"].get("url", {}).get("urls")
        self.pinned_tweet_ids = data["legacy"]["pinned_tweet_ids_str"]
        self.is_blue_verified = data["is_blue_verified"]
        self.verified = data["legacy"]["verified"]
        self.possibly_sensitive = data["legacy"]["possibly_sensitive"]
        self.can_dm = data['legacy']['can_dm']
        self.can_media_tag = data["legacy"]["can_media_tag"]
        self.want_retweets = data["legacy"]["want_retweets"]
        self.default_profile = data["legacy"]["default_profile"]
        self.default_profile_image = data["legacy"]["default_profile_image"]
        self.has_custom_timelines = data["legacy"]["has_custom_timelines"]
        self.followers_count = data["legacy"]["followers_count"]
        self.fast_followers_count = data["legacy"]["fast_followers_count"]
        self.normal_followers_count = data["legacy"]["normal_followers_count"]
        self.following_count = data["legacy"]["friends_count"]
        self.favourites_count = data["legacy"]["favourites_count"]
        self.listed_count = data["legacy"]["listed_count"]
        self.media_count = data["legacy"]["media_count"]
        self.statuses_count = data["legacy"]["statuses_count"]
        self.is_translator = data["legacy"]["is_translator"]
        self.translator_type = data["legacy"]["translator_type"]
        self.profile_interstitial_type = data["legacy"]["profile_interstitial_type"]
        self.withheld_in_countries = data["legacy"]["withheld_in_countries"]

    def __repr__(self) -> str:
        return f'<User id="{self.id}">'
