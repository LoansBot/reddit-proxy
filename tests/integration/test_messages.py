"""Verifies that we can send ourselves a message and read it"""
import unittest
import os
import pika
import json
import time
import helper

PIKA_PARAMETERS = pika.ConnectionParameters(
    os.environ['AMQP_HOST'],
    int(os.environ['AMQP_PORT']),
    os.environ['AMQP_VHOST'],
    pika.PlainCredentials(
        os.environ['AMQP_USERNAME'], os.environ['AMQP_PASSWORD']
    )
)


QUEUE = os.environ['AMQP_QUEUE']


RESPONSE_QUEUE = 'test_messages_resp_queue'


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

    def test_compose(self):
        self.channel.basic_publish(
            '',
            QUEUE,
            json.dumps({
                'type': 'compose',
                'response_queue': RESPONSE_QUEUE,
                'uuid': 'test_messages_A_uuid',
                'version_utc_seconds': 1,
                'sent_at': time.time(),
                'args': {
                    'recipient': os.environ['REDDIT_USERNAME'],
                    'subject': 'test_messages',
                    'body': 'This is a test *with* markdown'
                }
            })
        )
        body = helper.fetch_one(self, RESPONSE_QUEUE)
        self.assertEqual(
            body,
            {
                'uuid': 'test_messages_B_uuid',
                'type': 'success'
            }
        )

    def test_read(self):
        self.channel.basic_publish(
            '',
            QUEUE,
            json.dumps({
                'type': 'inbox',
                'response_queue': RESPONSE_QUEUE,
                'uuid': 'test_messages_B_uuid',
                'version_utc_seconds': 1,
                'sent_at': time.time(),
                'args': {}
            })
        )
        body = helper.fetch_one(self, RESPONSE_QUEUE)

        self.assertEqual(body.get('uuid'), 'test_messages_C_uuid')
        self.assertEqual(body.get('type'), 'copy')
        self.assertIsInstance(body.get('info'), dict)
        info = body['info']
        self.assertIsInstance(info.get('messages'), list)
        self.assertIsInstance(info.get('comments'), list)

        for msg in info['messages']:
            self.assertIsInstance(msg.get('fullname'), str)
            self.assertIsInstance(msg.get('subject'), str)
            self.assertIsInstance(msg.get('body'), str)
            self.assertIsInstance(msg.get('author'), str)
            self.assertIsInstance(msg.get('created_utc'), float)

    def test_mark_all_read(self):
        self.channel.basic_publish(
            '',
            QUEUE,
            json.dumps({
                'type': 'mark_all_read',
                'response_queue': RESPONSE_QUEUE,
                'uuid': 'test_messages_C_uuid',
                'version_utc_seconds': 1,
                'sent_at': time.time(),
                'args': {}
            })
        )
        body = helper.fetch_one(self, RESPONSE_QUEUE)
        self.assertEqual(
            body,
            {
                'uuid': 'test_messages_A_uuid',
                'type': 'success'
            }
        )


if __name__ == '__main__':
    unittest.main()
