"""Endpoints related to authorization"""
import requests
from base64 import b64encode


class LoginEndpoint:
    def __init__(self, default_headers):
        self.name = 'login'
        self.default_headers = default_headers

    def make_request(self, username, password, client_id, client_secret):
        """Login the given user. The result can be converted to an Auth using
        Auth.from_response

        :param username: The username to login
        :param password: The password for the account {username}
        :param client_id: The id of the app the user created
        :param client_secret: The secret for the app the user created
        """
        return requests.post(
            'https://www.reddit.com/api/v1/access_token',
            headers = {**self.default_headers, **{
                'Authorization': 'Basic ' + b64encode((client_id + ':' + client_secret).encode('ascii')).decode('ascii')
            }},
            data = {
                'grant_type': 'password',
                'username': username,
                'password': password
            }
        )


class RevokeAuthEndpoint:
    def __init__(self, default_headers):
        self.name = 'revoke_auth'
        self.default_headers = default_headers

    def make_request(self, auth):
        """Revokes the given authorization on reddit, ensuring that the token
        is useless.

        :param auth: the Auth to revoke
        """
        return requests.post(
            'https://www.reddit.com/api/v1/revoke_token',
            headers = self.default_headers,
            data = {
                'token': auth.access_token,
                'token_type_hint': 'access_token'
            }
        )


def register_endpoints(arr, headers):
    arr += [LoginEndpoint(headers), RevokeAuthEndpoint(headers)]
