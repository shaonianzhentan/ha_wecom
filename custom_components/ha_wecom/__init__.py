from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
from homeassistant.const import Platform

from .manifest import manifest
from .const import PLATFORMS

DOMAIN = manifest.domain

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    config = entry.data
    await register_mqtt(self.hass, config['topic'], config['key'])
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await discovery.async_load_platform(
        hass,
        Platform.NOTIFY,
        DOMAIN,
        {'name': config['uid'], 'entry_id': entry.entry_id, **config},
        {},
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data[DOMAIN].remove(entry.data['topic'])
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)