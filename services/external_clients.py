import environ
import requests

from services import ExternalServiceError

# Typed env reader. NOTE: this reads from os.environ.
# Make sure settings.py calls environ.Env.read_env(...) so .env is loaded.
env = environ.Env(
    HTTP_TIMEOUT_SECONDS=(float, 10.0),
)

# REQUIRED env vars (no defaults). If missing -> ImproperlyConfigured at startup.
CRM_USERS_URL = env("CRM_USERS_URL")
SUPPORT_POSTS_URL = env("SUPPORT_POSTS_URL")


class BaseHTTPClient:
    def __init__(self, timeout_seconds: float | None = None):
        self.timeout_seconds = timeout_seconds if timeout_seconds is not None else env("HTTP_TIMEOUT_SECONDS")

    def get_json(self, url: str):
        try:
            resp = requests.get(url, timeout=self.timeout_seconds)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.Timeout as e:
            raise ExternalServiceError(f"Timeout calling {url}") from e
        except requests.exceptions.RequestException as e:
            raise ExternalServiceError(f"HTTP error calling {url}: {e}") from e
        except ValueError as e:
            raise ExternalServiceError(f"Invalid JSON from {url}") from e

        if not isinstance(data, list):
            raise ExternalServiceError(f"Unexpected payload from {url}: expected list")
        return data


class CRMClient(BaseHTTPClient):
    def fetch_customers(self):
        return self.get_json(CRM_USERS_URL)


class SupportClient(BaseHTTPClient):
    def fetch_tickets(self):
        return self.get_json(SUPPORT_POSTS_URL)