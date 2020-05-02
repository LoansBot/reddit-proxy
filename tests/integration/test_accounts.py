"""Verify that we can view tjstretchalot's account"""
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


RESPONSE_QUEUE = 'accounts_resp_queue'


class CommentsTest(unittest.TestCase):
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

    def test_show_user(self):
        self.channel.basic_publish(
            '',
            QUEUE,
            json.dumps({
                'type': 'show_user',
                'response_queue': RESPONSE_QUEUE,
                'uuid': 'accounts-uuid',
                'version_utc_seconds': 1,
                'sent_at': time.time(),
                'args': {
                    'username': 'Tjstretchalot'
                }
            })
        )
        for (
                method_frame, properties, body_bytes
         ) in self.channel.consume(RESPONSE_QUEUE, inactivity_timeout=60):
            self.assertIsNotNone(method_frame)
            self.channel.basic_ack(method_frame.delivery_tag)
            body = json.loads(body_bytes.decode('utf-8'))
            break

        self.assertIsInstance(body, dict)
        self.assertEqual(body.get('status'), 200)
        self.assertEqual(body.get('type'), 'copy')
        self.assertEqual(body.get('uuid'), 'accounts-uuid')
        self.assertIsInstance(body.get('info'), dict)
        info = body['info']
        self.assertIsInstance(info.get('cumulative_karma'), int)
        self.assertIsInstance(info.get('created_at_utc_seconds'), float)
