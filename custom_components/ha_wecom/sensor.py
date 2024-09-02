from homeassistant.components.sensor import SensorEntity
from homeassistant.util.dt import now, get_default_time_zone
from .manifest import manifest

async def async_setup_entry(hass, config_entry, async_add_entities):    
    async_add_entities([WeComSensor(hass, config_entry)])

class WeComSensor(SensorEntity):

    def __init__(self, hass, entry):
        self._attr_unique_id = f'{entry.entry_id}-sensor'
        self.hass = hass
        uid = entry.data['uid']
        topic = entry.data['topic']
        self._attr_name = uid
        self._attr_icon = 'mdi:wechat'
        self._attr_device_info = manifest.device_info(uid, topic)
        self._attr_device_class = 'timestamp'
        self.ha_mqtt.on(f'{topic}message', self.mqtt_message)

    @property
    def ha_mqtt(self):
      return self.hass.data[manifest.domain]

    def mqtt_message(self, data):
        self._attr_native_value = now().replace(tzinfo=get_default_time_zone())

    async def async_update(self):
        self._attr_extra_state_attributes = {
          'connected': '连接成功' if self.ha_mqtt.is_connected else '断开连接'
        }