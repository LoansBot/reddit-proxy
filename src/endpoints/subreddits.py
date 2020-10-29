"""Contains endpoints related to a subreddit as a whole
"""
import requests


class SubredditModeratorsEndpoint:
    def __init__(self, default_headers):
        self.name = 'subreddit_moderators'
        self.default_headers = default_headers

    def make_request(self, subreddit, auth):
        """Fetch the list of moderators on a subreddit. This doesn't provide
        much information on each user which is great most of the time.

        Arguments:
        - `subreddit (str)`: The subreddit whose moderators should be fetched.
          May not be multiple subreddits.
        - `auth (Auth)`: Authorization to use for the request
        """
        return requests.get(
            f'https://oauth.reddit.com/r/{subreddit}/about/moderators',
            headers={**self.default_headers, **auth.get_auth_headers()}
        )


def register_endpoints(arr, headers):
    arr += [
        SubredditModeratorsEndpoint(headers)
    ]
