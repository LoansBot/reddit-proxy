"""This module provides hooks to message-related endpoints"""
import pytypeutils as tus


class InboxHandler:
    """Handles requests of type "inbox". This accepts no arguments, only
    returns unread, and has the response format:

    {
        "messages": [
            { "fullname": str, "subject": str, "body": str, "author": str, "created_utc": float },
            ...
        ],
        "comments": [
            {
                "fullname": str,
                "body": str,
                "author": str,
                "subreddit": str,
                "created_utc": float
            },
            ...
        ]
    }
    """
    def __init__(self):
        self.name = 'inbox'
        self.requires_delay = True

    def handle(self, reddit, auth, data):
        result = reddit.unread(25, None, None, auth)
        if result.status_code > 299:
            return result.status_code, None

        messages = []
        comments = []

        body = result.json()

        for child in body['data']['children']:
            if child['was_comment']:
                comments.append(
                    {
                        'fullname': child['name'],
                        'body': child['body'],
                        'author': child['author'],
                        'subreddit': child['subreddit'],
                        'created_utc': child['created_utc']
                    }
                )
            else:
                messages.append(
                    {
                        'fullname': child['name'],
                        'subject': child['subject'],
                        'body': child['body'],
                        'author': child['author'],
                        'created_utc': child['created_utc']
                    }
                )

        return result.status_code, {'messages': messages, 'comments': comments}


class ComposeHandler:
    """Handles requests of type "compose". This accepts 3 arguments - the
    recipient, the subject of the message, and the body of the message. The
    response is either a non-200 status code or success
    """
    def __init__(self):
        self.name = 'compose'
        self.requires_delay = True

    def handle(self, reddit, auth, data):
        recipient = data.get('recipient')
        subject = data.get('subject')
        body = data.get('body')

        tus.check(
            recipient=(recipient, str),
            subject=(subject, str),
            body=(body, str)
        )

        result = reddit.compose(recipient, subject, body, auth)
        if result.status_code > 299:
            return result.status_code, None
        return 'success', None


class MarkAllReadHandler:
    """Handles requests of the type "mark_all_read". Makrs the entire inbox
    as read. This returns either a non-200 status code or success.
    """
    def __init__(self):
        self.name = 'mark_all_read'
        self.requires_delay = True

    def handle(self, reddit, auth, data):
        result = reddit.mark_all_read(auth)
        if result.status_code > 299:
            return result.status_code, None
        return 'success', None


def register_handlers(handlers):
    handlers += [
        InboxHandler(),
        ComposeHandler(),
        MarkAllReadHandler()
    ]
