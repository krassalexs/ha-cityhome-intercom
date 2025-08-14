import logging
from datetime import timedelta
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.event import async_track_time_interval
from .const import DOMAIN, API, PARAM_ACCESS_TOKEN, PARAM_DEVICE_TOKEN
from .api import IntercomAPI

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.BUTTON, Platform.CAMERA]


async def async_setup(hass: HomeAssistant, config: dict):
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    api = IntercomAPI()
    api.set_tokens(
        entry.data.get(PARAM_ACCESS_TOKEN),
        entry.data.get(PARAM_DEVICE_TOKEN)
    )

    def update_entry(access_token, device_token):
        _LOGGER.debug("Updating entry with new tokens")
        new_data = entry.data.copy()
        new_data.update({
            PARAM_ACCESS_TOKEN: access_token,
            PARAM_DEVICE_TOKEN: device_token,
        })
        hass.config_entries.async_update_entry(entry, data=new_data)

    api.token_update_callback = update_entry
    hass.data[DOMAIN][API] = api

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    res = (await hass.config_entries.async_forward_entry_unload(entry, Platform.BUTTON) &
           await hass.config_entries.async_forward_entry_unload(entry, Platform.CAMERA))
    return res
