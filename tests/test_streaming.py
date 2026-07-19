"""Regression tests for the streaming event type union."""

import unittest
from typing import get_args

from twikit.streaming import DMUpdateEvent, DMTypingEvent, StreamEventType


class StreamEventTypeTest(unittest.TestCase):
    """Verify that every parsed stream event belongs to the public union."""

    def test_contains_each_direct_message_event_once(self):
        """Keep direct-message update and typing events in the union."""

        event_types = get_args(StreamEventType)

        self.assertEqual(event_types.count(DMUpdateEvent), 1)
        self.assertEqual(event_types.count(DMTypingEvent), 1)


if __name__ == "__main__":
    unittest.main()
