from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.helpers.entity import DeviceInfo
from .manifest import manifest

async def async_setup_entry(hass, config_entry, async_add_entities):
    async_add_entities([WecomTrackerEntity(hass, config_entry)])

class WecomTrackerEntity(TrackerEntity):

    def __init__(self, hass, entry):
        self.hass = hass
        self._attr_unique_id = f'{entry.entry_id}-tracker'
        uid = entry.data['uid']
        self.topic = entry.data['topic']
        self._attr_name = f'{uid}位置'
        self._attr_device_info = manifest.device_info(uid)
        self._attr_location_accuracy = 0
        self._attr_latitude = None
        self._attr_longitude = None
        self.ha_mqtt.on('location', self.mqtt_location)

    def mqtt_location(self, data):
      if data['topic'] == self.topic:
          self._attr_location_accuracy = data['precision']
          self._attr_latitude = data['latitude']
          self._attr_longitude = data['longitude']
          self.schedule_update_ha_state(True)

    @property
    def ha_mqtt(self):
      return self.hass.data[manifest.domain]

    @property
    def source_type(self) -> str:
        return SourceType.GPS

    @property
    def location_accuracy(self) -> int:
        return self._attr_location_accuracy

    @property
    def latitude(self) -> float | None:
        return self._attr_latitude

    @property
    def longitude(self) -> float | None:
        return self._attr_longitude