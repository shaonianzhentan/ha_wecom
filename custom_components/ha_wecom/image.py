from homeassistant.components.image import ImageEntity
from .manifest import manifest
from datetime import datetime

async def async_setup_entry(hass, config_entry, async_add_entities):    
    async_add_entities([WecomImage(hass, config_entry)])

class WecomImage(ImageEntity):

    def __init__(self, hass, entry):
        super().__init__(hass)
        self.hass = hass
        self._attr_unique_id = f'{entry.entry_id}-image'
        uid = entry.data['uid']
        topic = entry.data['topic']
        self._attr_name = f'{uid}图片'
        self._attr_device_info = manifest.device_info(uid, topic)
        self.ha_mqtt.on(f'{topic}image', self.mqtt_image)
        self._attr_image_url = 'https://www.home-assistant.io/images/favicon-192x192.png'

    def mqtt_image(self, data):
        self._cached_image = None
        self._attr_image_url = data['url']
        self._attr_image_last_updated = datetime.now()
        self.schedule_update_ha_state(True)

    @property
    def ha_mqtt(self):
        return self.hass.data[manifest.domain]