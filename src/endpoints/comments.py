"""Provides mappings for endpoints related to listings of comments"""
import requests


class SubredditCommentsListing:
    def __init__(self, default_headers):
        self.name = 'subreddit_comments'
        self.default_headers = default_headers

    def make_request(self, subreddits, limit, after, auth):
        """Fetch up to limit items after the given item. The items in the
        result are the newest limit items after the given after item. The
        subreddit may be multiple subreddits separated by a plus.

        :param subreddits: The subreddits to fetch comments from
        :param limit: The maximum number of comments to return. The server may
            return fewer.
        :param after: The after from the previous call if paginating.
        :param auth: The authorization to use, which will determine our ratelimiting.
        """
        data = {}
        if limit is not None:
            data['limit'] = limit
        if after is not None:
            data['after'] = after
        subreddits = '+'.join(subreddits)
        return requests.get(
            f'https://oauth.reddit.com/r/{subreddits}/comments',
            headers = {**self.default_headers, **auth.get_auth_headers()},
            data = data
        )


def register_endpoints(arr, headers):
    arr += [SubredditCommentsListing(headers)]
