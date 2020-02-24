"""This module provides the interface that handlers should use. Handlers should
not actually subclass this class, and handler modules should also have a
function register_handlers(handlers) which accepts a list of handlers and
appends any handlers defined in that module to it (instances, not the classes
themselves).
"""


class Handler:
    """A standard handler.

    :param name: The unique identifier for this handler, in snake_case.
    :param requires_delay: True if a delay is required, false otherwise
    """
    def handle(self, reddit, auth, data):
        """Handle an event with the given data and return the result and status
        code.

        :param reddit: the Reddit instance
        :param auth: The logged in users auth
        :param data: The dict of arguments passed as "args" in the packet
        :return status_code: The status code for the response. May have the
            special values 'success' or 'failure' to force the response
            type, otherwise should be an int.
        :return info: A dict containing additional information or None
        """
        pass
