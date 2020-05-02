"""Verify that we can fetch some links, where we try to get a selftext from
r/borrow and a link post from r/aww"""
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


RESPONSE_QUEUE = 'subreddit_links_resp_queue'


class LinksTest(unittest.TestCase):
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

    def test_fetch_one_selftext(self):
        self.channel.basic_publish(
            '',
            QUEUE,
            json.dumps({
                'type': 'subreddit_links',
                'response_queue': RESPONSE_QUEUE,
                'uuid': 'subreddit-links-uuid',
                'version_utc_seconds': 1,
                'sent_at': time.time(),
                'args': {
                    'subreddit': ['borrow'],
                    'limit': 1
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
        self.assertEqual(body.get('uuid'), 'subreddit-links-uuid')
        self.assertIsInstance(body.get('info'), dict)
        info = body['info']
        self.assertIsInstance(info.get("after"), (str, None))
        self.assertIsInstance(info.get('self'), list)
        self.assertIsInstance(info.get('url'), list)

        self_ = info['self']
        url = info['url']
        self.assertEqual(len(self_) + len(url), 1)

        if not self_:
            print('got link-post on r/borrow, skipping remaining selftext tests')
            return

        post = self_[0]
        self.assertIsInstance(post.get('fullname'), str)
        self.assertEqual(post['fullname'][:3], 't3_')
        self.assertIsInstance(post.get('title'), str)
        self.assertIsInstance(post.get('body'), str)
        self.assertIsNone(post.get('url'))
        self.assertIsInstance(post.get('author'), str)
        self.assertEqual(post.get('subreddit'), 'borrow')
        self.assertIsInstance(post.get('created_utc'), (int, float))

    def test_fetch_one_link(self):
        self.channel.basic_publish(
            '',
            QUEUE,
            json.dumps({
                'type': 'subreddit_links',
                'response_queue': RESPONSE_QUEUE,
                'uuid': 'subreddit-links-uuid-2',
                'version_utc_seconds': 1,
                'sent_at': time.time(),
                'args': {
                    'subreddit': ['aww'],
                    'limit': 1
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
        self.assertEqual(body.get('uuid'), 'subreddit-links-uuid-2')
        self.assertIsInstance(body.get('info'), dict)
        info = body['info']
        self.assertIsInstance(info.get("after"), (str, None))
        self.assertIsInstance(info.get('self'), list)
        self.assertIsInstance(info.get('url'), list)

        self_ = info['self']
        url = info['url']
        self.assertEqual(len(self_) + len(url), 1)

        if not url:
            print('got selftext on r/aww, skipping remaining linkpost tests')
            return

        post = url[0]
        self.assertIsInstance(post.get('fullname'), str)
        self.assertEqual(post['fullname'][:3], 't3_')
        self.assertIsInstance(post.get('title'), str)
        self.assertIsInstance(post.get('url'), str)
        self.assertIsNone(post.get('body'))
        self.assertIsInstance(post.get('author'), str)
        self.assertEqual(post.get('subreddit'), 'aww')
        self.assertIsInstance(post.get('created_utc'), (int, float))


if __name__ == '__main__':
    unittest.main()
