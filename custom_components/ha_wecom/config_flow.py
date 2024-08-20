from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
import uuid
from .manifest import manifest

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

        return self.async_create_entry(title=DOMAIN, data={ 'topic': topic, 'key': key })