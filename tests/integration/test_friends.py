"""Verify that we can ban/unban a user on /r/borrowtests"""
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
RESPONSE_QUEUE = 'friends_resp_queue'


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

    def test_ban_unban(self):
        self.channel.basic_publish(
            '',
            QUEUE,
            json.dumps({
                'type': 'ban_user',
                'response_queue': RESPONSE_QUEUE,
                'uuid': 'ban-user-uuid',
                'version_utc_seconds': 1,
                'sent_at': time.time(),
                'args': {
                    'subreddit': os.environ['REDDIT_MOD_SUBREDDIT'],
                    'username': 'foxk56',
                    'message': 'Test message',
                    'note': 'Test note'
                }
            })
        )
        body = helper.fetch_one(self, RESPONSE_QUEUE)
        self.assertEqual(
            body,
            {
                'uuid': 'ban-user-uuid',
                'type': 'success'
            }
        )
        self.channel.basic_publish(
            '',
            QUEUE,
            json.dumps({
                'type': 'unban_user',
                'response_queue': RESPONSE_QUEUE,
                'uuid': 'unban-user-uuid',
                'version_utc_seconds': 1,
                'sent_at': time.time(),
                'args': {
                    'subreddit': os.environ['REDDIT_MOD_SUBREDDIT'],
                    'username': 'foxk56'
                }
            })
        )
        body = helper.fetch_one(self, RESPONSE_QUEUE)
        self.assertEqual(
            body,
            {
                'uuid': 'unban-user-uuid',
                'type': 'success'
            }
        )


if __name__ == '__main__':
    unittest.main()
