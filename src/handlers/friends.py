"""This module provides hooks into the friends endpoints."""


class BanUserHandler:
    """Handles requests of the type "ban_user" and of the following form:
    {
        "subreddit": "some text",
        "username": "some text",
        "message": "some text", (sent to the user)
        "note": "some text" (for moderators)
    }

    and returns success/failure.
    """
    def __init__(self):
        self.name = 'ban_user'
        self.requires_delay = True

    def handle(self, reddit, auth, data):
        result = reddit.subreddit_friend(
            data['subreddit'], data['username'], 'banned', auth,
            ban_message=data.get('message'), ban_note=data.get('note')
        )
        if result.status_code > 299:
            return result.status_code, None
        return 'success', None


class UnbanUserHandler:
    """Handles requests of the type "unban_user" and of the following form:
    {
        "subreddit": "some text",
        "username": "some text"
    }

    and returns success/failure.
    """
    def __init__(self):
        self.name = 'unban_user'
        self.requires_delay = True

    def handle(self, reddit, auth, data):
        result = reddit.subreddit_unfriend(
            data['subreddit'], data['username'], 'banned', auth
        )
        if result.status_code > 299:
            return result.status_code, None
        return 'success', None


def register_handlers(handlers):
    handlers += [
        BanUserHandler(),
        UnbanUserHandler()
    ]
