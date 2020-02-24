"""Tests sending a ping packet through the amqp server"""
import unittest
import os
import pika
import json
import time


PIKA_PARAMETERS = pika.ConnectionParameters(
    os.environ['AMQP_HOST'],
    int(os.environ['AMQP_PORT']),
    os.environ['AMQP_VHOST'],
    pika.PlainCredentials(
        os.environ['AMQP_USERNAME'], os.environ['AMQP_PASSWORD']
    )
)


QUEUE = os.environ['AMQP_QUEUE']


RESPONSE_QUEUE = 'ping_resp_queue'


class PingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        amqp = pika.BlockingConnection(PIKA_PARAMETERS)
        channel = amqp.channel()
        channel.queue_declare(QUEUE)
        channel.queue_declare(RESPONSE_QUEUE)
        cls.channel = channel
        cls.amqp = amqp

    @classmethod
    def tearDownClass(cls):
        cls.channel.close()
        cls.amqp.close()

    def test_ping(self):
        self.channel.basic_publish(
            '',
            QUEUE,
            json.dumps({
                'type': '_ping',
                'response_queue': RESPONSE_QUEUE,
                'uuid': 'ping-uuid',
                'version_utc_seconds': 1,
                'sent_at': time.time(),
                'args': {}
            })
        )
        for method_frame, properties, body_bytes in self.channel.consume(RESPONSE_QUEUE, inactivity_timeout=5):
            self.assertIsNotNone(method_frame)
            self.channel.basic_ack(method_frame.delivery_tag)
            body = json.loads(body_bytes.decode('utf-8'))
            break

        self.assertEqual(
            body,
            {
                'uuid': 'ping-uuid',
                'type': 'success'
            }
        )


if __name__ == '__main__':
    unittest.main()
