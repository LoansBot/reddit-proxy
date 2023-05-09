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
        "link_karma": int,
        "comment_karma": int,
        "created_at_utc_seconds": float
    }
    """

    def __init__(self):
        self.name = "show_user"
        self.requires_delay = True

    def handle(self, reddit, auth, data):
        result = reddit.show_user(auth, data["username"])
        if result.status_code > 299:
            return result.status_code, None

        body = result.json()
        return result.status_code, {
            "cumulative_karma": (
                body["data"]["link_karma"] + body["data"]["comment_karma"]
            ),
            "link_karma": body["data"]["link_karma"],
            "comment_karma": body["data"]["comment_karma"],
            "created_at_utc_seconds": float(body["data"]["created_utc"]),
        }


class UserIsModeratorHandler:
    """Handles requests of type "user_is_moderator". This accepts data in the following
    form:
    {
        "subreddit": str,
        "username": str
    }

    And returns in the following form:

    {
        "moderator": bool
    }
    """

    def __init__(self):
        self.name = "user_is_moderator"
        self.requires_delay = True

    def handle(self, reddit, auth, data):
        result = reddit.user_is_moderator(auth, data["subreddit"], data["username"])
        if result.status_code > 299:
            return result.status_code, None

        body = result.json()
        rel_exists = any(
            True
            for ele in body["data"]["children"]
            if ele["name"].lower() == data["username"].lower()
        )

        return result.status_code, {"moderator": rel_exists}


class UserIsApprovedHandler:
    """Handles requests of type "user_is_approved". This accepts data in the following
    form:
    {
        "subreddit": str,
        "username": str
    }

    And returns in the following form:

    {
        "approved": bool
    }
    """

    def __init__(self):
        self.name = "user_is_approved"
        self.requires_delay = True

    def handle(self, reddit, auth, data):
        result = reddit.user_is_approved(auth, data["subreddit"], data["username"])
        if result.status_code > 299:
            return result.status_code, None

        body = result.json()
        rel_exists = any(
            True
            for ele in body["data"]["children"]
            if ele["name"].lower() == data["username"].lower()
        )

        return result.status_code, {"approved": rel_exists}


class UserIsBannedHandler:
    """Handles requests of type "user_is_banned". This accepts data in the following
    form:
    {
        "subreddit": str,
        "username": str
    }

    And returns in the following form:

    {
        "banned": bool
    }
    """

    def __init__(self):
        self.name = "user_is_banned"
        self.requires_delay = True

    def handle(self, reddit, auth, data):
        result = reddit.user_is_banned(auth, data["subreddit"], data["username"])
        if result.status_code > 299:
            return result.status_code, None

        body = result.json()
        rel_exists = any(
            True
            for ele in body["data"]["children"]
            if ele["name"].lower() == data["username"].lower()
        )

        return result.status_code, {"banned": rel_exists}


def register_handlers(handlers):
    handlers += [
        UserShowHandler(),
        UserIsModeratorHandler(),
        UserIsApprovedHandler(),
        UserIsBannedHandler(),
    ]
