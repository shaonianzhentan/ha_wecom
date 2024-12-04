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

    VERSION = 2

    def __init__(self):      
        self.key = str(uuid.uuid4()).replace('-', '')
        self.topic = str(uuid.uuid1()).replace('-', '')
        self.is_join = False

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:  
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=vol.Schema({
              vol.Required("host", default=f'broker.emqx.io'): str
            }))
        self.host = user_input.get('host')
        return await self.async_step_link()

    async def async_step_link(self, user_input: dict[str, Any] | None = None) -> FlowResult:      
        key = self.key
        topic = self.topic
        if user_input is None:
            server = 'emqx'
            if self.host.startswith("mqtt://"):
                server = 'local'
            DATA_SCHEMA = vol.Schema({
              vol.Required("key", default=f'HA:{key}#{topic}#{server}'): str
            })
            return self.async_show_form(step_id="link", data_schema=DATA_SCHEMA)

        # 等待关联
        ha_mqtt = await register_mqtt(self.hass, self.host, topic, key)
        result = await ha_mqtt.waiting_join(topic)
        if result is not None:
            self.is_join = True
            uid = result.get('uid')
            return self.async_create_entry(title=uid, data={
                'host': self.host,
                'uid': uid,
                'topic': topic,
                'key': key 
            })
        else:
            return self.async_abort(reason="cancel_join")

    def async_remove(self):
        if self.is_join == False and manifest.domain in self.hass.data:
            self.hass.data[manifest.domain].cancel_join(self.topic)