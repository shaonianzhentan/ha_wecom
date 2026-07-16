from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
from homeassistant.const import Platform

from .manifest import manifest
from .const import PLATFORMS
from .ha_mqtt import register_mqtt

DOMAIN = manifest.domain

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    config = entry.data
    await register_mqtt(hass, config['topic'], config['key'])
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
    result = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    ha_mqtt = hass.data.get(DOMAIN)
    if ha_mqtt is not None:
        ha_mqtt.remove(entry.data['topic'])
        # 最后一个条目卸载后释放共享连接，再次添加时由 register_mqtt 重建
        if not ha_mqtt.users:
            ha_mqtt.close()
            hass.data.pop(DOMAIN, None)
    return result