from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

import httpx

from twikit import Client


class ClientTransportTests(IsolatedAsyncioTestCase):
    async def test_explicit_transport_handles_request_without_network(self):
        def reply(request):
            return httpx.Response(200, json={'path': request.url.path})

        client = Client(transport=httpx.MockTransport(reply), trust_env=False)
        async with client.http:
            with patch.object(httpx.AsyncHTTPTransport, 'handle_async_request',
                              side_effect=AssertionError('unexpected network transport')):
                response = await client.http.get('https://example.invalid/probe')
        self.assertEqual(response.json(), {'path': '/probe'})
