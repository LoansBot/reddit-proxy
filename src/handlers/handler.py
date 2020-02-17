"""This module provides the interface that handlers should use. Handlers should
not actually subclass this class, and handler modules should also have a
function register_handlers(handlers) which accepts a list of handlers and
appends any handlers defined in that module to it (instances, not the classes
themselves).
"""

class Handler:
    """A standard handler.

    :param name: The unique identifier for this handler, in snake_case.
    """
    def handle(data):
        pass
