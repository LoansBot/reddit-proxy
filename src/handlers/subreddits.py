"""Handles for talking about a subreddit as a whole"""


class SubredditModeratorsHandler:
    """Handles requests of the form

    {
        "subreddit": str
    }

    and returns in the following form

    {
        "mods": [
            {
                "username": str,
                "mod_permissions": [str, ...]
            },
            ...
        ]
    }
    """
    def __init__(self):
        self.name = 'subreddit_moderators'
        self.requires_delay = True

    def handle(self, reddit, auth, data):
        subreddit = data['subreddit']
        result = reddit.subreddit_moderators(subreddit, auth)
        if result.status_code > 299:
            return result.status_code, None

        mods = []

        body = result.json()
        for child in body['data']['children']:
            mods.append({
                'username': child['name'],
                'mod_permissions': child['mod_permissions']
            })

        return result.status_code, {'mods': mods}


def register_handlers(handlers):
    handlers += [
        SubredditModeratorsHandler()
    ]
