"""This module provides hooks into the account endpoints."""


class UserShowHandler:
    """Handles requests of type "show_user". This accepts data in the following
    form:
    {
        "username": str
    }

    And returns in the following form:

    {
        "cumulative_karma": int,
        "created_at_utc_seconds": float
    }
    """
    def __init__(self):
        self.name = 'show_user'
        self.requires_delay = True

    def handle(self, reddit, auth, data):
        result = reddit.show_user(auth, data['username'])
        if result.status_code > 299:
            return result.status_code, None

        body = result.json()
        return result.status_code, {
            'cumulative_karma': body['data']['link_karma'] + body['data']['comment_karma'],
            'created_at_utc_seconds': float(body['data']['created_utc'])
        }


def register_handlers(handlers):
    handlers += [UserShowHandler()]