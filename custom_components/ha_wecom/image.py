from homeassistant.components.image import ImageEntity
from .manifest import manifest

async def async_setup_entry(hass, config_entry, async_add_entities):    
    async_add_entities([WecomImage(config_entry)])

class WecomImage(ImageEntity):

    def __init__(self, entry):
        self._attr_unique_id = f'{entry.entry_id}-image'
        uid = entry.data['uid']
        self.topic = entry.data['topic']
        self._attr_name = f'{uid}图片'
        self._attr_device_info = manifest.device_info(uid)

    @property
    def user(self):
        ha_mqtt = self.hass.data[manifest.domain]
        return ha_mqtt.get_user(self.topic)

    @cached_property
    def image_url(self) -> str | None:
        """Return URL of image."""
        return self.user.image_url