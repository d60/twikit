"""Tests for the optional Xquik search client."""

import os
import unittest
from unittest.mock import patch

import httpx
from twikit import XquikSearchClient


class FakeResponse:
    """Minimal HTTP response double for search tests."""

    def __init__(self, payload):
        """Store the JSON payload returned by the double."""

        self.payload = payload

    def json(self):
        """Return the configured JSON payload."""

        return self.payload

    def raise_for_status(self):
        """Represent a successful response."""

        return None


class ErrorResponse(FakeResponse):
    """HTTP response double that raises a server error."""

    def __init__(self):
        """Build a bound request and response for the HTTP error."""

        request = httpx.Request("GET", "https://xquik.com/api/v1/x/tweets/search")
        response = httpx.Response(500, request=request)
        super().__init__({})
        self.error = httpx.HTTPStatusError(
            "Server error",
            request=request,
            response=response,
        )

    def raise_for_status(self):
        """Raise the configured HTTP status error."""

        raise self.error


class FakeClient:
    """HTTP client double that records requests and lifecycle state."""

    def __init__(self, payload=None, response=None):
        """Configure the payload or explicit response returned by the client."""

        self.payload = payload
        self.response = response
        self.requests = []
        self.closed = False

    def get(self, url, headers, params):
        """Record one GET request and return the configured response."""

        self.requests.append({"url": url, "headers": headers, "params": params})
        if self.response:
            return self.response
        return FakeResponse(self.payload)

    def close(self):
        """Record that the client was closed."""

        self.closed = True


class XquikSearchClientTest(unittest.TestCase):
    """Verify search validation, mapping, errors, and client ownership."""

    def test_requires_api_key(self):
        """Reject construction when no explicit or environment key exists."""

        original_api_key = os.environ.pop("XQUIK_API_KEY", None)
        try:
            with self.assertRaises(ValueError):
                XquikSearchClient(api_key="", client=FakeClient({}))
        finally:
            if original_api_key is not None:
                os.environ["XQUIK_API_KEY"] = original_api_key

    def test_uses_env_api_key_when_not_passed(self):
        """Use XQUIK_API_KEY when the constructor receives no key."""

        original_api_key = os.environ.get("XQUIK_API_KEY")
        try:
            os.environ["XQUIK_API_KEY"] = "env-key"

            client = XquikSearchClient(client=FakeClient({}))

            self.assertEqual(client.api_key, "env-key")
        finally:
            if original_api_key is None:
                os.environ.pop("XQUIK_API_KEY", None)
            else:
                os.environ["XQUIK_API_KEY"] = original_api_key

    def test_search_maps_tweets_and_pagination(self):
        """Map tweet fields and pagination while preserving request inputs."""

        fake_client = FakeClient(
            {
                "tweets": [
                    {
                        "id": "123",
                        "text": "hello",
                        "createdAt": "2026-06-30T00:00:00.000Z",
                        "likeCount": 4,
                        "retweetCount": 3,
                        "replyCount": 2,
                        "quoteCount": 1,
                        "author": {"username": "xquik", "name": "Xquik"},
                    }
                ],
                "has_next_page": True,
                "next_cursor": "cursor-1",
            }
        )

        result = XquikSearchClient(api_key="test-key", client=fake_client).search(
            "x data",
            limit=5,
            cursor="cursor-0",
        )

        self.assertEqual(len(result.tweets), 1)
        self.assertEqual(result.tweets[0].id, "123")
        self.assertEqual(result.tweets[0].author_username, "xquik")
        self.assertEqual(result.tweets[0].favorite_count, 4)
        self.assertTrue(result.has_next_page)
        self.assertEqual(result.next_cursor, "cursor-1")
        self.assertEqual(
            fake_client.requests[0]["url"],
            "https://xquik.com/api/v1/x/tweets/search",
        )
        self.assertEqual(fake_client.requests[0]["headers"]["x-api-key"], "test-key")
        self.assertEqual(fake_client.requests[0]["params"]["q"], "x data")
        self.assertEqual(fake_client.requests[0]["params"]["limit"], 5)
        self.assertEqual(fake_client.requests[0]["params"]["cursor"], "cursor-0")
        self.assertFalse(fake_client.closed)

    def test_search_propagates_time_filters(self):
        """Send documented time filters with the search request."""

        fake_client = FakeClient({"tweets": []})

        XquikSearchClient(api_key="test-key", client=fake_client).search(
            "x data",
            since_time="2026-06-29T00:00:00Z",
            until_time="2026-06-30T00:00:00Z",
        )

        params = fake_client.requests[0]["params"]
        self.assertEqual(params["sinceTime"], "2026-06-29T00:00:00Z")
        self.assertEqual(params["untilTime"], "2026-06-30T00:00:00Z")

    def test_search_validates_inputs(self):
        """Reject malformed query, type, limit, and time values locally."""

        client = XquikSearchClient(api_key="test-key", client=FakeClient({}))

        with self.assertRaises(ValueError):
            client.search("")
        with self.assertRaises(ValueError):
            client.search("x data", query_type="Recent")
        with self.assertRaises(ValueError):
            client.search("x data", limit=0)
        with self.assertRaises(ValueError):
            client.search("x data", since_time="not-a-date")

    def test_search_handles_sparse_tweet_payloads(self):
        """Normalize sparse tweets and skip non-object entries."""

        fake_client = FakeClient(
            {
                "tweets": [
                    {"id": "missing-author", "text": "no author"},
                    {"id": "bad-author", "text": "bad author", "author": "xquik"},
                    "not-a-tweet",
                    {
                        "id": "messy-counts",
                        "text": "counts",
                        "likeCount": " 4 ",
                        "retweetCount": "+3",
                        "replyCount": True,
                        "quoteCount": "1,200",
                    },
                ],
            }
        )

        result = XquikSearchClient(api_key="test-key", client=fake_client).search("x data")

        self.assertEqual(len(result.tweets), 3)
        tweets_by_id = {tweet.id: tweet for tweet in result.tweets}
        self.assertIsNone(tweets_by_id["missing-author"].author_username)
        self.assertIsNone(tweets_by_id["bad-author"].author_name)
        self.assertEqual(tweets_by_id["messy-counts"].favorite_count, 4)
        self.assertEqual(tweets_by_id["messy-counts"].retweet_count, 3)
        self.assertEqual(tweets_by_id["messy-counts"].reply_count, 1)
        self.assertEqual(tweets_by_id["messy-counts"].quote_count, 1200)

    def test_search_rejects_non_object_response(self):
        """Reject JSON roots that are not objects."""

        client = XquikSearchClient(api_key="test-key", client=FakeClient([]))

        with self.assertRaises(ValueError):
            client.search("x data")

    def test_search_propagates_http_errors(self):
        """Propagate HTTP status errors from the transport."""

        client = XquikSearchClient(
            api_key="test-key",
            client=FakeClient(response=ErrorResponse()),
        )

        with self.assertRaises(httpx.HTTPStatusError):
            client.search("x data")

    def test_search_closes_owned_client(self):
        """Close internally created clients after the request."""

        owned_clients = []

        class OwnedFakeClient(FakeClient):
            """Track each client created by the search implementation."""

            def __init__(self, *args, **kwargs):
                """Create and register an internally owned client double."""

                super().__init__({"tweets": []})
                owned_clients.append(self)

        with patch("twikit.xquik.httpx.Client", OwnedFakeClient):
            XquikSearchClient(api_key="test-key").search("x data")

        self.assertEqual(len(owned_clients), 1)
        self.assertTrue(owned_clients[0].closed)


if __name__ == "__main__":
    unittest.main()
