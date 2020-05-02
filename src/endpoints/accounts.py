"""Provides endpoints for fetching a users karma and account age."""
import requests


class UserShowEndpoint:
    def __init__(self, default_headers):
        self.name = 'show_user'
        self.default_headers = default_headers

    def make_request(self, auth, username):
        """Fetch the user account information of the given username.

        :param username: The reddit username of the account to check on.
        """
        return requests.get(
            f'https://oauth.reddit.com/user/{username}/about',
            headers={**self.default_headers, **auth.get_auth_headers()}
        )


class UserIsModeratorEndpoint:
    def __init__(self, default_headers):
        self.name = 'user_is_moderator'
        self.default_headers = default_headers

    def make_request(self, auth, subreddit, username):
        """Fetch the user list with the given username. If the user is a
        moderator of the given subreddit this will have one relationship
        which is that user, otherwise it will have no relationships.

        :param subreddit: The subreddit to check for a relationshp for
        :param username: The username to check for a relationship for
        """
        return requests.get(
            f'https://oauth.reddit.com/r/{subreddit}/about/moderators',
            headers={**self.default_headers, **auth.get_auth_headers()},
            params={'user': username}
        )


class UserIsApprovedEndpoint:
    def __init__(self, default_headers):
        self.name = 'user_is_approved'
        self.default_headers = default_headers

    def make_request(self, auth, subreddit, username):
        """Fetch the user list with the given username. If the user is an
        approved submitter of the subreddit this is a user listing with just
        that user / subreddit relationship, otherwise this will have no
        relationships.

        :param subreddit: The subreddit to check for a relationship on
        :param username: The username to check for a relationship with
        """
        return requests.get(
            f'https://oauth.reddit.com/r/{subreddit}/about/contributors',
            headers={**self.default_headers, **auth.get_auth_headers()},
            params={'user': username}
        )


def register_endpoints(arr, headers):
    arr += [
        UserShowEndpoint(headers),
        UserIsModeratorEndpoint(headers),
        UserIsApprovedEndpoint(headers)
    ]
