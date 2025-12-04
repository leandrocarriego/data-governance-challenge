import logging
import requests

from src.settings import settings
from src.services.mercadolibre.exceptions import MeliExtractError

logger = logging.getLogger(__name__)


class MeliExtractService:
    """Client wrapper to interact with MercadoLibre items and auth endpoints."""

    def __init__(
        self,
        base_url: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        timeout: int = 20,
    ) -> None:
        self.base_url = base_url or settings.meli_base_url
        self.access_token = access_token or settings.meli_access_token
        self.refresh_token = refresh_token or settings.meli_refresh_token
        self.client_id = client_id or settings.meli_client_id
        self.client_secret = client_secret or settings.meli_client_secret
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        """Return auth headers or raise if access token is missing."""

        if not self.access_token:
            raise MeliExtractError("MELI access token not configured.")

        return {"Authorization": f"Bearer {self.access_token}"}

    def _can_refresh(self) -> bool:
        """Tell if we have enough data to refresh the token."""

        return bool(self.refresh_token and self.client_id and self.client_secret)

    def _refresh_access_token(self) -> None:
        """Refresh and update access/refresh tokens."""

        if not self._can_refresh():
            raise MeliExtractError(
                "Cannot refresh token: client_id/client_secret/refresh_token missing."
            )

        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
        }
        refresh_token_url = f"{self.base_url}/oauth/token"

        response = requests.post(refresh_token_url, data=data, timeout=self.timeout)

        if not response.ok:
            raise MeliExtractError(
                f"Token refresh failed {response.status_code}: {response.text}"
            )

        payload = response.json()
        self.access_token = payload.get("access_token")
        self.refresh_token = payload.get("refresh_token", self.refresh_token)

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Execute an HTTP request and refresh on 401/403."""

        headers = self._headers()
        response = requests.request(
            method, url, headers=headers, timeout=self.timeout, **kwargs
        )

        if response.status_code in (401, 403) and self._can_refresh():
            self._refresh_access_token()
            response = requests.request(
                method, url, headers=self._headers(), timeout=self.timeout, **kwargs
            )

        if not response.ok:
            logger.error(
                "MELI request failed %s %s status=%s body=%s",
                method,
                url,
                response.status_code,
                response.text,
            )

        return response

    def extract_item_description(self, item_id: str) -> dict:
        """Fetch item description payload by item id."""

        url = f"{self.base_url}/items/{item_id}/description"

        logger.info("Extracting description for item %s", item_id)
        
        response = self._request("GET", url)

        if not response.ok:
            raise MeliExtractError(
                f"Item description failed {response.status_code}: {response.text}"
            )
        
        return response.json()
