"""Verify that we can fetch some comments on /r/borrow"""
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


RESPONSE_QUEUE = 'subreddit_comments_resp_queue'


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

    def test_fetch_one_comment(self):
        self.channel.basic_publish(
            '',
            QUEUE,
            json.dumps({
                'type': 'subreddit_comments',
                'response_queue': RESPONSE_QUEUE,
                'uuid': 'subreddit-comments-uuid',
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
        self.assertEqual(body.get('uuid'), 'subreddit-comments-uuid')
        self.assertIsInstance(body.get('info'), dict)
        info = body['info']
        self.assertIsInstance(info.get("after"), (str, None))
        self.assertIsInstance(info.get('comments'), list)

        comments = info['comments']
        self.assertEqual(len(comments), 1)
        comment = comments[0]
        self.assertIsInstance(comment, dict)
        self.assertIsInstance(comment.get('fullname'), str)
        self.assertEqual(comment['fullname'][:3], 't1_')
        self.assertIsInstance(comment.get('body'), str)
        self.assertIsInstance(comment.get('author'), str)
        self.assertIsInstance(comment.get('link_fullname'), str)
        self.assertIsInstance(comment.get('link_author'), str)
        self.assertEqual(comment['link_fullname'][:3], 't3_')
        self.assertEqual(comment.get('subreddit'), 'borrow')
        self.assertIsInstance(comment.get('created_utc'), (int, float))
        # we give some wiggle room because our clock might be off
        self.assertTrue(comment['created_utc'] < time.time() + 10)

    def test_pagination(self):
        # related to loansboat#59
        self.channel.basic_publish(
            '',
            QUEUE,
            json.dumps({
                'type': 'subreddit_comments',
                'response_queue': RESPONSE_QUEUE,
                'uuid': 'subreddit-comments-uuid1',
                'version_utc_seconds': 1,
                'sent_at': time.time(),
                'args': {
                    'subreddit': ['borrow'],
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

        self.assertEqual(body.get('status'), 200)
        self.assertEqual(body.get('type'), 'copy')
        self.assertEqual(body.get('uuid'), 'subreddit-comments-uuid1')

        comment_fullnames = [c['fullname'] for c in body['info']['comments']]
        after = body['info']['after']
        self.assertIn(after, comment_fullnames)

        self.channel.basic_publish(
            '',
            QUEUE,
            json.dumps({
                'type': 'subreddit_comments',
                'response_queue': RESPONSE_QUEUE,
                'uuid': 'subreddit-comments-uuid2',
                'version_utc_seconds': 1,
                'sent_at': time.time(),
                'args': {
                    'subreddit': ['borrow'],
                    'after': after
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

        self.assertEqual(body.get('status'), 200)
        self.assertEqual(body.get('type'), 'copy')
        self.assertEqual(body.get('uuid'), 'subreddit-comments-uuid2')

        after_comment_fullnames = [c['fullname'] for c in body['info']['comments']]
        self.assertNotEqual(comment_fullnames, after_comment_fullnames)
        for after_fullname in after_comment_fullnames:
            self.assertNotIn(after_fullname, comment_fullnames)


if __name__ == '__main__':
    unittest.main()
