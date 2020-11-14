"""Contains endpoints for fetching listings of subreddit links"""
import requests


class SubredditLinksListing:
    def __init__(self, default_headers):
        self.name = 'subreddit_links'
        self.default_headers = default_headers

    def make_request(self, subreddits, limit, after, auth):
        """Fetch up to limit items after the given item. The items in the
        result are the newest limit items after the given after item. The
        subreddit may be multiple subreddits separated by a plus.

        :param subreddits: The subreddits to fetch comments from
        :param limit: The maximum number of comments to return. The server may
            return fewer.
        :param after: The after from the previous call if paginating.
        :param auth: The authorization to use, which will determine our ratelimiting.
        """
        data = {}
        if limit is not None:
            data['limit'] = limit
        if after is not None:
            data['after'] = after
        subreddits = '+'.join(subreddits)
        return requests.get(
            f'https://oauth.reddit.com/r/{subreddits}/new',
            headers={**self.default_headers, **auth.get_auth_headers()},
            data=data
        )


class FlairLinkEndpoint:
    def __init__(self, default_headers):
        self.name = 'flair_link'
        self.default_headers = default_headers

    def make_request(self, subreddit, link_fullname, css_class, text, auth):
        """Flairs the given link using the given css class identifier.

        :param subreddit: The name of the subreddit in which the link to
            flair resides.
        :param link_fullname: The fullname of the link (starting with t3_) to
            flair.
        :param css_class: The ID of the CSS class within the subreddit to flair
            the link with.
        :param text: The text to associate with the flair.
        :param auth: The authorization for the request.
        """
        return requests.post(
            f'https://oauth.reddit.com/r/{subreddit}/api/flair',
            headers={**self.default_headers, **auth.get_auth_headers()},
            data={
                'api_type': 'json',
                'link': link_fullname,
                'css_class': css_class,
                'text': text
            }
        )


def register_endpoints(arr, headers):
    arr += [
        SubredditLinksListing(headers),
        FlairLinkEndpoint(headers)
    ]
