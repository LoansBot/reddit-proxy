"""Endpoints related to forming relationships between people and subreddits.
"""
from .endpoint import Endpoint
import requests


class SubredditFriendEndpoint(Endpoint):
    def __init__(self, default_headers):
        self.name = 'subreddit_friend'
        self.default_headers = default_headers

    def make_request(
            self, subreddit, username, relationship, auth,
            ban_message=None, ban_reason='other', ban_note=None):
        """Forms a relationship between a user and a subreddit. Acceptable
        relationships are:

        - `banned`: The user cannot interact with the subreddit.
        - `contributor`: Flags a user as able to participate in the subreddit even
        if they otherwise would not to. Does not override "banned"

        :param subreddit: The subreddit in the relationship, e.g., borrow
        :param username: The user in the relationship, e.g., Tjstretchalot
        :param relationship: The relationship to form (typically "banned" or "contributor")
        :param auth: Authorization to use with the request
        :param ban_message: The message to send to the user for why they were banned. Ignored
        if the relationship is not banned
        :param ban_reason: The reason for the ban, acts as an enum. Typically the string 'other'.
            Ignored if the relationship is not banned.
        :param ban_note: The private moderator note for why the user was banned. Ignored if
        the relationship is not banned.
        """
        data = {
            'name': username,
            'type': relationship
        }
        if relationship == 'banned':
            data['ban_message'] = ban_message
            data['ban_reason'] = ban_reason
            data['note'] = ban_note

        return requests.post(
            f'https://oauth.reddit.com/r/{subreddit}/api/friend?api_type=json',
            headers={**self.default_headers, **auth.get_auth_headers()},
            data=data
        )


class SubredditUnfriendEndpoint(Endpoint):
    def __init__(self, default_headers):
        self.name = 'subreddit_unfriend'
        self.default_headers = default_headers

    def make_request(self, subreddit, username, relationship, auth):
        """Removes the given relationship between the subreddit and the user.

        :param subreddit: The subreddit in the relationship, e.g., borrow
        :param username: The user in the relationship, e.g., tjstretchalot
        :param relationship: The relationship to remove, e.g., banned
        :param auth: The authorization to use
        """
        return requests.post(
            f'https://oauth.reddit.com/r/{subreddit}/api/unfriend',
            headers={**self.default_headers, **auth.get_auth_headers()},
            data={
                'name': username,
                'type': relationship
            }
        )


def register_endpoints(arr, headers):
    arr += [
        SubredditFriendEndpoint(headers),
        SubredditUnfriendEndpoint(headers)
    ]
