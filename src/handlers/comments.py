"""This module provides hooks to comment listing endpoints"""


class SubredditCommentsHandler:
    """Handles requests of type "subreddit_comments". This accepts data in the
    following form:
    {
        "subreddits": [str, ...],
        "limit": int,
        "after": str
    }

    And returns in the following form:

    {
        "comments": [
            {
                "fullname": str, "body": str, "author": str,
                "link_fullname": str,  "subreddit": str, "created_utc": float
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
        result = reddit.subreddit_comments(data['subreddit'], data.get('limit'), data.get('after'), auth)
        if result.status_code > 299:
            return result.status_code, None

        comments = []

        body = result.json()
        after = body['data'].get('after')

        for child in body['data']['children']:
            child = child['data']
            comments.append(
                {
                    'fullname': child['name'],
                    'body': child['body'],
                    'author': child['author'],
                    'link_fullname': child['link_id'],
                    'subreddit': child['subreddit'],
                    'created_utc': child['created_utc']
                }
            )

        comments.sort(key=lambda c: -c['created_utc'])
        if data.get('limit'):
            limit = data['limit']
            if len(comments) > limit:
                comments = comments[:limit]

        return result.status_code, { 'comments': comments, 'after': after }


def register_handlers(handlers):
    handlers += [SubredditCommentsHandler()]