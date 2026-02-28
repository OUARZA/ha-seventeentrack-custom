"""17TRACK v2.4 API client."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from aiohttp import ClientError, ClientSession

API_BASE_URL = "https://api.17track.net/track/v2.4"


class SeventeenTrackError(Exception):
    """Base API error."""


@dataclass(frozen=True, order=True)
class SeventeenTrackPackage:
    """Normalized package data from 17TRACK."""

    tracking_number: str
    status: str
    friendly_name: str | None = None
    info_text: str | None = None
    timestamp: datetime | None = None
    origin_country: str | None = None
    destination_country: str | None = None
    package_type: str | None = None
    tracking_info_language: str | None = None
    location: str | None = None


class SeventeenTrackApiClient:
    """Minimal 17TRACK API client using v2.4 endpoints."""

    def __init__(self, session: ClientSession, api_key: str) -> None:
        self._session = session
        self._api_key = api_key

    async def async_validate_token(self) -> bool:
        """Validate API key. Any non-auth error means token is accepted."""
        try:
            await self._request("gettrackinfo", [])
        except SeventeenTrackError as err:
            return "invalid" not in str(err).lower()
        return True

    async def async_get_packages(self) -> list[SeventeenTrackPackage]:
        """Fetch all registered packages and normalize payload."""
        payload = await self._request("gettrackinfo", [])

        entries: list[dict[str, Any]] = []
        if isinstance(payload, list):
            entries = [item for item in payload if isinstance(item, dict)]
        elif isinstance(payload, dict):
            candidates = payload.get("accepted") or payload.get("items") or []
            if isinstance(candidates, list):
                entries = [item for item in candidates if isinstance(item, dict)]

        return [self._to_package(item) for item in entries if item.get("number")]

    async def async_add_package(self, tracking_number: str, title: str) -> None:
        """Register a package."""
        await self._request("register", [{"number": tracking_number, "title": title}])

    async def async_archive_package(self, tracking_number: str) -> None:
        """Delete package tracking from 17TRACK."""
        await self._request("delete", [{"number": tracking_number}])

    async def _request(self, endpoint: str, body: list[dict[str, Any]]) -> Any:
        headers = {"17token": self._api_key, "Content-Type": "application/json"}
        url = f"{API_BASE_URL}/{endpoint}"

        try:
            response = await self._session.post(url, headers=headers, json=body)
            result = await response.json(content_type=None)
        except (ClientError, ValueError) as err:
            raise SeventeenTrackError(f"Request failed: {err}") from err

        if response.status >= 400:
            raise SeventeenTrackError(self._extract_error(result, response.status))

        code = result.get("code") if isinstance(result, dict) else None
        if code not in (0, 200, None):
            raise SeventeenTrackError(self._extract_error(result, response.status))

        if isinstance(result, dict):
            return result.get("data", result)
        return result

    def _to_package(self, item: dict[str, Any]) -> SeventeenTrackPackage:
        tracking = item.get("track_info") or {}
        latest_status = tracking.get("latest_status") or {}
        latest_event = tracking.get("latest_event") or tracking.get("last_event") or {}

        status = (
            latest_status.get("status")
            or latest_status.get("description")
            or item.get("status")
            or "Unknown"
        )

        info_text = (
            latest_event.get("description")
            or latest_event.get("event")
            or latest_status.get("sub_status")
        )

        location = latest_event.get("location")
        timestamp = _parse_datetime(
            latest_event.get("time_iso")
            or latest_event.get("time_utc")
            or latest_event.get("time_raw")
        )

        package_info = tracking.get("package_info") or {}
        origin_info = package_info.get("origin_info") or {}
        destination_info = package_info.get("destination_info") or {}

        return SeventeenTrackPackage(
            tracking_number=item.get("number", ""),
            status=str(status),
            friendly_name=item.get("title"),
            info_text=info_text,
            timestamp=timestamp,
            origin_country=origin_info.get("country") or origin_info.get("from"),
            destination_country=destination_info.get("country")
            or destination_info.get("to"),
            package_type=package_info.get("package_type"),
            tracking_info_language=item.get("lang"),
            location=location,
        )

    def _extract_error(self, result: Any, status: int) -> str:
        if not isinstance(result, dict):
            return f"API error (HTTP {status})"

        data = result.get("data", {})
        errors = data.get("errors") if isinstance(data, dict) else None
        if errors and isinstance(errors, list):
            first = errors[0]
            if isinstance(first, dict):
                message = first.get("message")
                if message:
                    return str(message)

        message = result.get("message")
        return str(message or f"API error (HTTP {status})")


def _parse_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None

    candidate = raw.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(candidate)
    except ValueError:
        return None
