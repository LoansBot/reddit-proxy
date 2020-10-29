"""Tests sending a ping packet through the amqp server"""
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


RESPONSE_QUEUE = 'subreddits__resp_queue'


class SubredditsTest(unittest.TestCase):
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
                'type': 'subreddit_moderators',
                'response_queue': RESPONSE_QUEUE,
                'uuid': 'sub-mods-uuid',
                'version_utc_seconds': 1,
                'sent_at': time.time(),
                'args': {
                    'subreddit': os.environ['REDDIT_MOD_SUBREDDIT']
                }
            })
        )
        body = helper.fetch_one(self, RESPONSE_QUEUE)

        self.assertIsInstance(body, dict)
        self.assertEqual(body.get('uuid'), 'sub-mods-uuid')
        self.assertEqual(body.get('type'), 'copy')
        self.assertIsInstance(body.get('info'), dict)

        info = body['info']
        self.assertIsInstance(info.get('mods'), list)
        for mod in info['mods']:
            self.assertIsInstance(mod, dict)
            self.assertIsInstance(mod.get('username'), str)
            self.assertIsInstance(mod.get('mod_permissions'), list)
            for mod_perm in mod['mod_permissions']:
                self.assertIsInstance(mod_perm, str)

        expected_mod_unms = frozenset((os.environ['REDDIT_USERNAME'], 'USLBot', 'Tjstretchalot'))
        sorted_mods = sorted(info['mods'], key=lambda x: x['username'])
        sorted_expected_mods = [{'username': k, 'mod_permissions': ['all']} for k in sorted(expected_mod_unms)]
        self.assertEqual(sorted_mods, sorted_expected_mods)


if __name__ == '__main__':
    unittest.main()
