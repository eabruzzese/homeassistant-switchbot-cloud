"""The SwitchBot Cloud integration."""
from __future__ import annotations
from datetime import timedelta
import logging
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from switchbot import Device, SwitchBot # pylint: disable=import-error

from .coordinator import SwitchBotDataUpdateCoordinator
from .const import DATA_COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["cover"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SwitchBot Cloud from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    switchbot = SwitchBot(token=entry.data[CONF_API_TOKEN])

    async def async_update_data() -> Dict[str, Device]:
        try:
            # Fetch each cloud-enabled device and its status.
            devices = [d for d in await hass.async_add_executor_job(switchbot.devices) if d.cloud_enabled]
            for device in devices:
                # TODO Remove this line once the fix is merged: https://github.com/jonghwanhyeon/python-switchbot/pull/11
                device.client = switchbot.client
                device._cached_status = await hass.async_add_executor_job(device.status)
            return {device.id: device for device in devices}
        except RuntimeError as err:
            raise ConfigEntryAuthFailed from err
        except IOError as err:
            raise UpdateFailed(
                f'Error communicating with the SwitchBot API: {err}') from err

    # Create a coordinator that can be used across all platforms.
    coordinator: SwitchBotDataUpdateCoordinator = hass.data[DOMAIN].setdefault(DATA_COORDINATOR, SwitchBotDataUpdateCoordinator(
        hass,
        _LOGGER,
        api=SwitchBot(token=entry.data[CONF_API_TOKEN]),
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=30)
    ))

    # Fetch initial data and raise an error if it fails.
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {DATA_COORDINATOR: coordinator}

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

        if len(hass.config_entries.async_entries(DOMAIN)) == 0:
            hass.data.pop(DOMAIN)

    return unload_ok
