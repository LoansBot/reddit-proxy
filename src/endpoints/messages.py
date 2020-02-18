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
            'https://oauth.reddit.com/api/message/unread',
            headers = {**self.default_headers, **auth.get_auth_headers()},
            data = data
        )


def register_endpoints(arr, headers):
    arr += [UnreadEndpoint(headers)]
