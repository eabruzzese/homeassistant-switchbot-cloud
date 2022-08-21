from typing import Any
from switchbot import SwitchBot # pylint: disable=import-error
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


class SwitchBotDataUpdateCoordinator(DataUpdateCoordinator):
    """A thin wrapper around the DataUpdateCoordinator to store an API instance."""

    api: SwitchBot

    def __init__(self, *args: Any, api: SwitchBot, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.api = api
