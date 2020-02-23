"""This module contains ping/pong handlers"""

class PingHandler:
    """Responds with a success packet and no data."""
    def __init__(self):
        self.name = '_ping'
        self.requires_delay = False

    def handle(self, reddit, auth, data):
        return 'success', None


def register_handlers(handlers):
    handlers += [PingHandler()]
