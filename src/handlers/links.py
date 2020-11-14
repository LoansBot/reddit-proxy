"""This module provides hooks to list listing endpoints"""


class SubredditLinksHandler:
    """Handles requests of type "subreddit_links". This accepts data in the
    following form:
    {
        "subreddits": [str, ...],
        "limit": int,
        "after": str
    }

    And returns in the following form:

    {
        "self": [
            {
                "fullname": str, "title": str, "body": str, "author": str,
                "subreddit": str, "created_utc": float
            },
            ...
        ],
        "url": [
            {
                "fullname": str, "title": str, "url": str, "author": str,
                "subreddit": str, "created_utc": float
            }
        ],
        "after": str or None
    }
    """
    def __init__(self):
        self.name = 'subreddit_links'
        self.requires_delay = True

    def handle(self, reddit, auth, data):
        if data.get('limit', 1) < 1:
            return 400, None
        result = reddit.subreddit_links(
            data['subreddit'], data.get('limit'), data.get('after'), auth)
        if result.status_code > 299:
            return result.status_code, None

        self_ = []
        url = []

        body = result.json()
        after = body['data'].get('after')

        for child in body['data']['children']:
            child = child['data']
            if child.get('banned_at_utc') is not None:
                continue
            if child.get('removed'):
                continue

            gen_info = {
                'fullname': child['name'],
                'title': child['title'],
                'author': child['author'],
                'subreddit': child['subreddit'],
                'created_utc': child['created_utc']
            }

            if child['is_self']:
                self_.append(
                    {
                        'body': child['selftext'],
                        **gen_info
                    }
                )
            else:
                url.append(
                    {
                        'url': child['url'],
                        **gen_info
                    }
                )

        self_.sort(key=lambda c: -c['created_utc'])
        url.sort(key=lambda c: -c['created_utc'])
        if data.get('limit'):
            limit = data['limit']
            while len(self_) + len(url) > limit:
                if self_ and (not url or self_[-1]['created_utc'] < url[-1]['created_utc']):
                    self_.pop()
                else:
                    url.pop()

        return result.status_code, {'self': self_, 'url': url, 'after': after}


class FlairLinkHandler:
    """Handles requests of the form "flair_link". This accepts data in the
    following form:
    {
        "subreddit": str,
        "link_fullname": str,
        "css_class": str,
        "text": str
    }

    And returns success/failure.
    """
    def __init__(self):
        self.name = 'flair_link'
        self.requires_delay = True

    def handle(self, reddit, auth, data):
        if data.get('limit', 1) < 1:
            return 400, None
        result = reddit.flair_link(
            data['subreddit'], data.get('link_fullname'),
            data.get('css_class'), data.get('text'), auth)
        if result.status_code > 299:
            return result.status_code, None
        return 'success', None


def register_handlers(handlers):
    handlers += [SubredditLinksHandler(), FlairLinkHandler()]
