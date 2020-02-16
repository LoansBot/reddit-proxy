"""The interface for things within this packag. It is not recommended that the
endpoints actually subclass this class, since it confused linters to subclass
and change the accepted arguments.

Every .py file in this folder should have a
"register_endpoints(endpoints, headers)" function as a module-level function
which adds the endpoints (as instances) defined in that module to the given
list, using the given default headers.
"""


class Endpoint:
    """Describes an endpoint that can be handled by the reddit abstraction.

    :param default_headers: The default headers to pass to requests.
        For example, the user agent.
    :param name: The snakecase name for this endpoint internally for the
        LoansBot. For example users_me.
    """
    def __init__(self, default_headers):
        pass

    def make_request(self, *args, **kwargs):
        """Make the appropriate request to the given endpoint and return the
        response from requests
        """
        pass
