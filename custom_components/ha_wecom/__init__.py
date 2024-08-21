from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .manifest import manifest
from .const import PLATFORMS
from .ha_mqtt import HaMqtt

DOMAIN = manifest.domain

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    config = entry.data
    topic = config['topic']
    key = config['key']
    hass.data[DOMAIN] = await hass.async_add_executor_job(HaMqtt, hass, {
        'topic': topic,
        'key': key
    })

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data[DOMAIN].close()
    del hass.data[DOMAIN]
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
