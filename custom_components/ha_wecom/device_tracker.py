from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.helpers.entity import DeviceInfo
from .manifest import manifest

async def async_setup_entry(hass, config_entry, async_add_entities):
    async_add_entities([WecomTrackerEntity(config_entry)])

class WecomTrackerEntity(TrackerEntity):

    def __init__(self, entry):
        self._attr_unique_id = f'{entry.entry_id}-tracker'
        uid = entry.data['uid']
        self.topic = entry.data['topic']
        self._attr_name = f'{uid}位置'
        self._attr_device_info = manifest.device_info(uid)

    @property
    def user(self):
        ha_mqtt = self.hass.data[manifest.domain]
        return ha_mqtt.get_user(self.topic)

    @property
    def source_type(self) -> str:
        raise 'gps'

    @cached_property
    def location_accuracy(self) -> int:
        return self.user.precision

    @cached_property
    def latitude(self) -> float | None:
        return self.user.latitude

    @cached_property
    def longitude(self) -> float | None:
        return self.user.longitude