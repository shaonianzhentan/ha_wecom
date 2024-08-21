from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo

from .manifest import manifest

async def async_setup_entry(hass, config_entry, async_add_entities):
    ha_mqtt = hass.data[manifest.domain]
    async_add_entities([WeComSensor(config_entry, ha_mqtt)])

class WeComSensor(SensorEntity):

    def __init__(self, entry, ha_mqtt):
        self._attr_unique_id = entry.entry_id
        self._attr_name = entry.data['name']
        self._attr_icon = 'mdi:wechat'
        self._attr_device_info = DeviceInfo(
            name=manifest.name,
            manufacturer='shaonianzhentan',
            model=manifest.domain,
            configuration_url=manifest.documentation,
            identifiers={(manifest.domain, 'shaonianzhentan')},
        )
        self.ha_mqtt = ha_mqtt
        self._attr_extra_state_attributes = {
          'receive_time': None
        }

    @property
    def state(self):
      return '连接成功' if self.ha_mqtt.is_connected else '断开连接'

    async def async_update(self):
      self._attr_extra_state_attributes = {
        'receive_time': self.ha_mqtt.msg_time
      }