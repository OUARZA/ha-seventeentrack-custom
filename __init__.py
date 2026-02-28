"""The seventeentrack component."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import SeventeenTrackApiClient, SeventeenTrackError
from .const import DOMAIN
from .coordinator import SeventeenTrackCoordinator
from .services import async_setup_services

PLATFORMS: list[Platform] = [Platform.SENSOR]

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the 17Track component."""

    async_setup_services(hass)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up 17Track from a config entry."""

    session = async_get_clientsession(hass)
    client = SeventeenTrackApiClient(session=session, api_key=entry.data[CONF_API_KEY])

    try:
        if not await client.async_validate_token():
            raise ConfigEntryNotReady("Invalid 17TRACK API token")
    except SeventeenTrackError as err:
        raise ConfigEntryNotReady from err

    seventeen_coordinator = SeventeenTrackCoordinator(hass, entry, client)

    await seventeen_coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = seventeen_coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
