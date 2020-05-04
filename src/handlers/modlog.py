"""This provides hooks into moderator log endpoints"""


class ModLogHandler:
    """Handles requests of type "modlog". This accepts data in the
    following form:
    {
        "subreddits": [str, ...],
        "limit": int,
        "after": str
    }

    And returns in the following form:

    {
        "actions": [
            {
                "target_fullname": str, "target_author": str,
                "mod": str, "action": str, "details": str,
                "subreddit": str, "created_utc": float
            },
            ...
        ],
        "after": str or None
    }
    """
    def __init__(self):
        self.name = 'subreddit_comments'
        self.requires_delay = True

    def handle(self, reddit, auth, data):
        # We want to maintain consistency; anything that accepts a subreddit
        # can also accept multiple subreddits separated by '+'
        subreddits = []
        for sub in data['subreddits']:
            for real_sub in sub.split('+'):
                subreddits.append(real_sub)

        result = reddit.modlog(
            '+'.join(subreddits), data.get('limit'), data.get('after'),
            None, auth
        )
        if result.status_code > 299:
            return result.status_code, None

        actions = []

        body = result.json()
        after = body['data'].get('after')

        for child in body['data']['children']:
            child = child['data']
            actions.append(
                {
                    'target_fullname': child.get('target_fullname'),
                    'target_author': child.get('target_author'),
                    'mod': child['mod'],
                    'action': child['action'],
                    'details': child.get('details'),
                    'subreddit': child['subreddit'],
                    'created_utc': float(child['created_utc'])
                }
            )

        actions.sort(key=lambda c: -c['created_utc'])
        if data.get('limit'):
            limit = data['limit']
            if len(actions) > limit:
                actions = actions[:limit]

        return result.status_code, {'actions': actions, 'after': after}


def register_handlers(handlers):
    handlers += [
        ModLogHandler()
    ]
