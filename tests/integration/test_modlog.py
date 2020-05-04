"""Tests fetching some stuff from a modlog"""
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


RESPONSE_QUEUE = 'modlog_queue'


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

    def test_modlog(self):
        self.channel.basic_publish(
            '',
            QUEUE,
            json.dumps({
                'type': 'modlog',
                'response_queue': RESPONSE_QUEUE,
                'uuid': 'modlog-uuid',
                'version_utc_seconds': 1,
                'sent_at': time.time(),
                'args': {
                    'subreddits': [os.environ['REDDIT_MOD_SUBREDDIT']],
                    'limit': 7
                }
            })
        )
        body = helper.fetch_one(self, RESPONSE_QUEUE)

        self.assertEqual(body.get('type'), 'copy')
        self.assertIsInstance(body.get('info'), 'dict')

        info = body['info']
        self.assertIsInstance(info.get('after'), (type(None), str))
        self.assertIsInstance(info.get('actions'), list)
        for act in info['actions']:
            self.assertIsInstance(act.get('target_fullname'), (type(None), str))
            self.assertIsInstance(act.get('target_author'), (type(None), str))
            self.assertIsInstance(act.get('mod'), str)
            self.assertIsInstance(act.get('action'), str)
            self.assertIsInstance(act.get('details'), (type(None), str))
            self.assertIsInstance(act.get('subreddit'), str)
            self.assertIsInstance(act.get('created_utc'), float)

        self.assertLessEqual(len(info['actions']), 7)


if __name__ == '__main__':
    unittest.main()
