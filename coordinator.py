"""Coordinator for 17Track."""

from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import slugify

from .api import SeventeenTrackApiClient, SeventeenTrackError, SeventeenTrackPackage
from .const import (
    CONF_SHOW_ARCHIVED,
    CONF_SHOW_DELIVERED,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LOGGER,
)


@dataclass
class SeventeenTrackData:
    """Class for handling the data retrieval."""

    summary: dict[str, dict[str, Any]]
    live_packages: dict[str, SeventeenTrackPackage]


class SeventeenTrackCoordinator(DataUpdateCoordinator[SeventeenTrackData]):
    """Class to manage fetching 17Track data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: SeventeenTrackApiClient,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.show_delivered = self.config_entry.options[CONF_SHOW_DELIVERED]
        self.account_id = config_entry.unique_id or config_entry.entry_id

        self.show_archived = self.config_entry.options[CONF_SHOW_ARCHIVED]
        self.client = client

    async def _async_update_data(self) -> SeventeenTrackData:
        """Fetch data from 17Track API."""

        try:
            packages = await self.client.async_get_packages()
        except SeventeenTrackError as err:
            raise UpdateFailed(err) from err

        summary_dict: dict[str, dict[str, Any]] = {}
        live_packages_dict: dict[str, SeventeenTrackPackage] = {}

        for package in sorted(packages):
            live_packages_dict[package.tracking_number] = package
            status_slug = slugify(package.status)
            if status_slug not in summary_dict:
                summary_dict[status_slug] = {
                    "quantity": 0,
                    "packages": [],
                    "status_name": package.status,
                }

            summary_dict[status_slug]["quantity"] += 1
            summary_dict[status_slug]["packages"].append(package)

        return SeventeenTrackData(
            summary=summary_dict, live_packages=live_packages_dict
        )
