"""Describes a reddit authorized user."""
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Auth:
    access_token: str
    token_type: str
    expires_at: datetime
    scope: str

    def get_auth_headers(self):
        return {'Authorization': f'bearer {self.access_token}'}

    @classmethod
    def from_response(cls, resp):
        resp.raise_for_status()
        parsed = resp.json()
        return cls(
            access_token=parsed['access_token'],
            token_type=parsed['token_type'],
            expires_at=datetime.now() + timedelta(seconds=parsed['expires_in']),
            scope=parsed['scope']
        )
