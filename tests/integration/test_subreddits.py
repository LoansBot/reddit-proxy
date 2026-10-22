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

        # The roster is not ours to pin.  This used to assert the exact set
        # {REDDIT_USERNAME, USLBot, Tjstretchalot}: USLBot was this account
        # before it was renamed to LoansBot, and the old name now belongs to
        # somebody else, so the assertion failed for a reason that had nothing
        # to do with the proxy.  What actually matters is that the endpoint
        # returns the subreddit's moderators and that the account we
        # authenticate as is one of them -- which is also what proves the
        # configured subreddit is one this account can moderate.
        mods = {mod['username'] for mod in info['mods']}
        self.assertTrue(mods, 'no moderators returned')
        self.assertIn(os.environ['REDDIT_USERNAME'], mods)


if __name__ == '__main__':
    unittest.main()
