"""Support for SwitchBot curtains."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    DEVICE_CLASS_CURTAIN,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_SET_POSITION,
    SUPPORT_STOP,
    CoverEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

if TYPE_CHECKING:
    from switchbot_cloud.devices import Curtain

from .const import DATA_COORDINATOR, DOMAIN, TYPE_CURTAIN
from .coordinator import SwitchBotDataUpdateCoordinator

# Initialize the logger
_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Switchbot curtains based on a config entry."""
    coordinator: SwitchBotDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]

    async_add_entities([
        SwitchBotCurtain(coordinator, device)
        for device in coordinator.data.values()
        # Only include curtains
        if device.type == TYPE_CURTAIN and
        # ... that are calibrated
        device.calibrated and
        # ... and that are either ungrouped, or the master within their group.
        (not device.grouped or device.master)
    ])


class SwitchBotCurtain(CoordinatorEntity, CoverEntity, RestoreEntity):
    """Representation of a SwitchBot curtain roller."""

    coordinator: SwitchBotDataUpdateCoordinator
    device_class = DEVICE_CLASS_CURTAIN
    supported_features = (
        SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_SET_POSITION
    )

    def __init__(self, coordinator: SwitchBotDataUpdateCoordinator, device: Curtain):
        super().__init__(coordinator)
        self.device = device

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "SwitchBot",
            "model": "Curtain"
        }

    @property
    def unique_id(self) -> str | None:
        return self.device.id

    @property
    def name(self) -> str | None:
        return self.device.name

    @property
    def current_cover_position(self) -> int | None:
        position = self.device._cached_status.get('slide_position')
        if position is not None:
            position = 100 - (5 * round(position / 5))
        return position

    @property
    def is_closed(self) -> bool | None:
        if self.current_cover_position is None:
            return None
        return self.current_cover_position <= 20

    async def _command(self, command: str, parameter: str | None = None):
        """Execute a device command asynchronously."""
        await self.hass.async_add_executor_job(self.device.command, command, parameter)

    async def _set_position(self, position: str | int):
        """Open the cover."""
        await self._command("set_position", f"0,ff,{100 - position}")

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        _LOGGER.debug(f"SwitchBot about to open curtain {self.name} ({self.unique_id})")
        self._attr_is_opening = True
        self.async_write_ha_state()
        await self._set_position(100)

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        _LOGGER.debug(f"SwitchBot about to close curtain {self.name} ({self.unique_id})")
        self._attr_is_closing = True
        self.async_write_ha_state()
        await self._set_position(0)

    async def async_set_cover_position(self, **kwargs):
        """Close the cover."""
        position = kwargs.get(ATTR_POSITION)
        _LOGGER.debug(f"SwitchBot about to set {self.name} ({self.unique_id}) position to {position}")
        await self._set_position(100 - position)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        device = self.coordinator.data[self.unique_id]
        is_moving = device._cached_status["moving"]

        self.device = device
        self._attr_is_opening = self.is_opening and is_moving
        self._attr_is_closing = self.is_closing and is_moving

        self.async_write_ha_state()
