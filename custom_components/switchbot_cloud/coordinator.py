from typing import TYPE_CHECKING, Any
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

if TYPE_CHECKING:
    from switchbot_cloud import SwitchBot


class SwitchBotDataUpdateCoordinator(DataUpdateCoordinator):
    """A thin wrapper around the DataUpdateCoordinator to store an API instance."""

    api: SwitchBot

    def __init__(self, *args: Any, api: SwitchBot, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.api = api
