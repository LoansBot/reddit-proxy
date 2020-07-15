"""Provides mappings to endpoints related to the standard reddit inbox"""
import requests


class UnreadEndpoint:
    def __init__(self, default_headers):
        self.name = 'unread'
        self.default_headers = default_headers

    def make_request(self, limit, after, before, auth):
        """Fetch up to limit items either after after, before before, or from
        the beginning. Only one of after and before should be set.

        :param limit: The maximum number of items to return (default 25, max
            100)
        :param after: The fullname to start the listing at, or None if either
            before is set or you want to start at the beginning
        :param before: The fullname to end the listing at, or None if either
            after is set or you want to start at the beginning
        :param auth: The Auth of the account to get the inbox of
        """
        data = {}
        if limit is not None:
            data['limit'] = limit
        if after is not None:
            data['after'] = after
        if before is not None:
            data['before'] = before
        return requests.get(
            'https://oauth.reddit.com/message/unread',
            headers={**self.default_headers, **auth.get_auth_headers()},
            data=data
        )


class ComposeEndpoint:
    def __init__(self, default_headers):
        self.name = 'compose'
        self.default_headers = default_headers

    def make_request(self, recipient, subject, body, auth):
        """Sends a request to the given recipient which has the given title
        and body. The body may be formatted with markdown.

        :param recipient: The string recipient, typically /u/uname or /r/sub
        :param subject: The string subject to send, shorter is better
        :param body: The body in markdown format
        """
        return requests.post(
            f'https://oauth.reddit.com/api/compose',
            headers={**self.default_headers, **auth.get_auth_headers()},
            data={
                'api_type': 'json',
                'subject': subject,
                'text': body,
                'to': recipient
            }
        )


class MarkAllReadEndpoint:
    def __init__(self, default_headers):
        self.name = 'mark_all_read'
        self.default_headers = default_headers

    def make_request(self, auth):
        """Marks the entire inbox as read."""
        return requests.post(
            f'https://oauth.reddit.com/api/read_all_messages',
            headers={**self.default_headers, **auth.get_auth_headers()},
        )


def register_endpoints(arr, headers):
    arr += [
        UnreadEndpoint(headers),
        ComposeEndpoint(headers),
        MarkAllReadEndpoint(headers)
    ]
