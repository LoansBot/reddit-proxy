"""Provides mappings for endpoints related to listings of comments"""
import requests


class SubredditCommentsListing:
    def __init__(self, default_headers):
        self.name = 'subreddit_comments'
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
            f'https://oauth.reddit.com/r/{subreddits}/comments',
            headers={**self.default_headers, **auth.get_auth_headers()},
            data=data
        )


class PostCommentEndpoint:
    def __init__(self, default_headers):
        self.name = 'post_comment'
        self.default_headers = default_headers

    def make_request(self, parent, text, auth):
        """Post a response to the fullname identified by 'parent' with the
        markdown text 'text'

        :param parent: The parent fullname to respond to
        :param text: The markdown to respond with
        :param auth: The authorization to use
        """
        return requests.post(
            'https://oauth.reddit.com/api/comment',
            headers={**self.default_headers, **auth.get_auth_headers()},
            data={'thing_id': parent, 'text': text}
        )


class LookupCommentEndpoint:
    def __init__(self, default_headers):
        self.name = 'lookup_comment'
        self.default_headers = default_headers

    def make_request(self, link_id, comment_id, auth):
        """Fetch the comment within the given link id with the given id. This returns
        an array with two listings, one of which (typically the first) is for the link
        and the other of which (typically the second) is for the comment.

        :param link_id: The id of the link, i.e., t3_xyz, that the comment is in
        :param comment_id: The id of the comment, i.e., t1_abc
        :param auth: The authorization to use
        """
        return requests.get(
            'https://oauth.reddit.com/comments/{}/loansbot/{}'.format(
                link_id[3:],
                comment_id[3:]
            )
        )


def register_endpoints(arr, headers):
    arr += [
        SubredditCommentsListing(headers),
        PostCommentEndpoint(headers),
        LookupCommentEndpoint(headers)
    ]
