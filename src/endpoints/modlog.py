"""Provides mappings to endpoints related to the moderator log"""
import requests


class ModLogEndpoint:
    def __init__(self, default_headers):
        self.name = 'modlog'
        self.default_headers = default_headers

    def make_request(self, subreddit, limit, after, before, auth):
        """Fetch up to limit items either after after, before before, or from
        the beginning of time for the given subreddit. Only one of after and
        before should be set.

        :param subreddit: The subreddit (or multiple joined by +) to get the
            moderator actions from
        :param limit: The maximum number of items to return (default 25, max
            100)
        :param after: The fullname to start the listing at, or None if either
            before is set or you want to start at the beginning
        :param before: The fullname to end the listing at, or None if either
            after is set or you want to start at the beginning
        :param auth: The authorization method
        """
        data = {}
        if limit is not None:
            data['limit'] = limit
        if after is not None:
            data['after'] = after
        if before is not None:
            data['before'] = before
        return requests.get(
            f'https://oauth.reddit.com/r/{subreddit}/about/log',
            headers={**self.default_headers, **auth.get_auth_headers()},
            data=data
        )


def register_endpoints(arr, headers):
    arr += [
        ModLogEndpoint(headers)
    ]
