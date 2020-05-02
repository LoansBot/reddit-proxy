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


def register_endpoints(arr, headers):
    arr += [
        UserShowEndpoint(headers)
    ]
