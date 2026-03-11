import secrets
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client.client import Client


class CastleToken:
    """
    Handles Castle Token generation for Twitter API requests.
    The token is cached for 1 minute to avoid unnecessary API calls.

    Parameters
    ----------
    client : Client
        The Twitter client instance
    api_key : str | None, default=None
        Optional API key for castle.botwitter.com
        - Without API key: 3 requests/second, 100 requests/hour (default rate limits)
        - With API key: Custom rate limits, higher quotas, priority support
    """

    def __init__(self, client: 'Client', api_key: str | None = None) -> None:
        self.client = client
        self.api_key = api_key
        self._castle_token: str | None = None
        self._cuid: str | None = None
        self._token_timestamp: float | None = None

    def _generate_cuid(self) -> str:
        """
        Generate a 32-character hexadecimal string for use as cuid.
        Example: 169c90ba59a6f01cc46e69d2669e080b
        """
        return secrets.token_hex(16)

    async def generate_castle_token(self) -> str:
        """
        Generate a new Castle token by:
        1. Generating a 32-character hex string (cuid)
        2. Setting it as the __cuid cookie
        3. Sending a POST request to https://castle.botwitter.com/generate-token
        4. Returning the Castle token from the response

        Rate Limits:
        - Default (no API key): 3 requests/second, 100 requests/hour

        Returns
        -------
        str
            The generated Castle token
        """
        # Generate cuid
        self._cuid = self._generate_cuid()

        # Set __cuid cookie
        self.client.http.cookies.set('__cuid', self._cuid)

        # Prepare request data
        payload = {
            'userAgent': self.client._user_agent,
            'cuid': self._cuid
        }

        # Prepare headers with optional API key authentication
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        # Send POST request to castle token API
        response = await self.client.http.post(
            'https://castle.botwitter.com/generate-token',
            json=payload,
            headers=headers
        )

        # Extract and cache the castle token from response
        response_data = response.json()
        self._castle_token = response_data.get('token', '')
        self._token_timestamp = time.time()

        return self._castle_token

    async def get_castle_token(self) -> str:
        """
        Get the cached Castle token or generate a new one if not cached or expired.
        Token cache expires after 60 seconds.

        Returns
        -------
        str
            The Castle token
        """
        if self._castle_token is None or self._token_timestamp is None:
            return await self.generate_castle_token()

        # Check if token is older than 60 seconds
        if time.time() - self._token_timestamp > 60:
            return await self.generate_castle_token()

        return self._castle_token
