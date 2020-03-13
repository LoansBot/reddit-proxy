"""Contains utility functions for tests"""
import json


def fetch_one(self, queue):
    """Fetch one message from the given queue"""
    for method_frame, properties, body_bytes in self.channel.consume(queue, inactivity_timeout=5):
        self.assertIsNotNone(method_frame)
        self.channel.basic_ack(method_frame.delivery_tag)
        return json.loads(body_bytes.decode('utf-8'))
