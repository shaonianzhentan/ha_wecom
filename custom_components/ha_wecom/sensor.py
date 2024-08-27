from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
import pytz
from .manifest import manifest

async def async_setup_entry(hass, config_entry, async_add_entities):    
    async_add_entities([WeComSensor(config_entry)])

class WeComSensor(SensorEntity):

    def __init__(self, entry):
        self._attr_unique_id = entry.entry_id
        uid = entry.data['uid']
        self.topic = entry.data['topic']
        self._attr_name = uid
        self._attr_icon = 'mdi:wechat'
        self._attr_device_info = DeviceInfo(
            name=uid,
            manufacturer='shaonianzhentan',
            model='wecom',
            configuration_url=manifest.documentation,
            identifiers={(manifest.domain, 'shaonianzhentan', uid)},
        )
        self._attr_device_class = 'timestamp'

    @property
    def ha_mqtt(self):
      return self.hass.data[manifest.domain]

    async def async_update(self):
      user = self.ha_mqtt.get_user(self.topic)
      if user.msg_time is not None:
          time_zone = pytz.timezone(self.hass.config.time_zone)
          self._attr_native_value = time_zone.localize(user.msg_time)

      self._attr_extra_state_attributes = {
        'connected': '连接成功' if self.ha_mqtt.is_connected else '断开连接'
      }