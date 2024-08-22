"""Notify.Events platform for notify component."""
from __future__ import annotations

import logging

from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_TITLE,
    ATTR_TARGET,
    BaseNotificationService,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from .manifest import manifest

def get_service(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
) -> WecomNotificationService:
    return WecomNotificationService(hass, discovery_info)

class WecomNotificationService(BaseNotificationService):

    def __init__(self, hass, config):
        self.topic = config.get("topic")

    @property
    def ha_mqtt(self):
        return self.hass.data[manifest.domain]

    def send_message(self, message, **kwargs):
        """Send a message."""
        data = kwargs.get(ATTR_DATA) or {}
        target = kwargs.get(ATTR_TARGET) or []
        title = kwargs.get(ATTR_TITLE, message)
        self.ha_mqtt.publish_server(self.topic, 'push', {
            'msgtype': 'text',
            'text': {
                'content': message
            }
        })