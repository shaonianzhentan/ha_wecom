from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
import uuid
from .manifest import manifest
from .ha_mqtt import HaMqtt

DOMAIN = manifest.domain
DATA_SCHEMA = vol.Schema({})

class SimpleConfigFlow(ConfigFlow, domain=DOMAIN):

    VERSION = 2

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
      
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)
  
        key = str(uuid.uuid4()).replace('-', '')
        topic = str(uuid.uuid1()).replace('-', '')

        # 等待关联
        ha_mqtt = await hass.async_add_executor_job(HaMqtt, hass, {
            'topic': topic,
            'key': key
        })
        wecom_key = f'HA:{token}#{topic}'
        print(wecom_key)
        result = await ha_mqtt.waiting_join()
        print(result)
        ha_mqtt.close()
        return self.async_create_entry(title=DOMAIN, data={
            'name': result.get('name'),
            'topic': topic, 
            'key': key 
        })