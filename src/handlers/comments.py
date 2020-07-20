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
                "link_fullname": str, "link_author": str, "subreddit": str,
                "created_utc": float
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
        result = reddit.subreddit_comments(
            data['subreddit'], data.get('limit'), data.get('after'),
            auth
        )
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
                    'link_author': child['link_author'],
                    'subreddit': child['subreddit'],
                    'created_utc': child['created_utc']
                }
            )

        comments.sort(key=lambda c: -c['created_utc'])
        if data.get('limit'):
            limit = data['limit']
            if len(comments) > limit:
                comments = comments[:limit]

        return result.status_code, {'comments': comments, 'after': after}


class PostCommentHandler:
    """Handles requests of type "post_comment". This accepts data in the
    following form:
    {
        "parent": str,
        "text": str
    }

    And returns success/failure status code.
    """
    def __init__(self):
        self.name = 'post_comment'
        self.requires_delay = True

    def handle(self, reddit, auth, data):
        res = reddit.post_comment(data['parent'], data['text'], auth)
        if res.status_code > 299:
            return res.status_code, None
        return 'success', None


class LookupCommentHandler:
    """Handles requests of the form "lookup_comment". This accepts data in the
    form

    {
        "link_fullname": "t3_xyz",
        "comment_fullname": "t1_abc"
    }

    And returns a single comment, as if from SubredditCommentsHandler.
    """
    def __init__(self):
        self.name = 'lookup_comment'
        self.requires_delay = True

    def handle(self, reddit, auth, data):
        res = reddit.lookup_comment(data['link_fullname'], data['comment_fullname'], auth)
        if res.status_code > 299:
            return res.status_code, None

        body = res.json()
        if len(body) != 2:
            return 404, None

        if body[0]['data']['dist'] is not None:
            comment_listing = body[1]
            link_listing = body[0]
        else:
            comment_listing = body[0]
            link_listing = body[1]

        if comment_listing['data']['dist'] is not None:
            return 404, None

        children = comment_listing['data']['children']
        if not children:
            return 404, None

        child = children[0]
        if child['kind'] != 't1':
            raise Exception(f'bad child in comments listing: {comment_listing} (expected kind=t1)')

        link_children = link_listing['data']['children']
        if not link_children or link_children[0]['kind'] != 't3':
            raise Exception(f'bad child in link listing: {link_listing} (expected kind=t3)')

        link_child = link_children[0]['data']
        child = child['data']
        return res.status_code, {
            'fullname': child['name'],
            'body': child['body'],
            'author': child['author'],
            'link_fullname': link_child['name'],
            'link_author': link_child['author'],
            'subreddit': child['subreddit'],
            'created_utc': child['created_utc']
        }


def register_handlers(handlers):
    handlers += [
        SubredditCommentsHandler(),
        PostCommentHandler(),
        LookupCommentHandler()
    ]
