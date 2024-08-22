from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
import uuid
from .manifest import manifest
from .ha_mqtt import HaMqtt, register_mqtt

DOMAIN = manifest.domain
DATA_SCHEMA = vol.Schema({})

class SimpleConfigFlow(ConfigFlow, domain=DOMAIN):

    VERSION = 1

    def __init__(self):      
        self.key = str(uuid.uuid4()).replace('-', '')
        self.topic = str(uuid.uuid1()).replace('-', '')

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:      
        key = self.key
        topic = self.topic
        if user_input is None:
            DATA_SCHEMA = vol.Schema({
              vol.Required("key", default=f'HA:{key}#{topic}'): str
            })
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

        # 等待关联
        ha_mqtt = await register_mqtt(self.hass, topic, key)
        result = await ha_mqtt.waiting_join(topic)
        print(result)
        return self.async_create_entry(title=DOMAIN, data={
            'uid': result.get('uid'),
            'topic': topic,
            'key': key 
        })