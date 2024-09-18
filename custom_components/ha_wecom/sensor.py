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
        self._attr_should_poll = False
        self._attr_name = uid
        self._attr_icon = 'mdi:wechat'
        self._attr_device_info = manifest.device_info(uid, topic)
        self._attr_device_class = 'timestamp'
        self.msg_type = None
        self.msg_data = None
        self.ha_mqtt.on(f'{topic}message', self.mqtt_message)
        self.update_attributes()

    @property
    def ha_mqtt(self):
      return self.hass.data[manifest.domain]

    def mqtt_message(self, data):
        msg_type = data['type']
        msg_data = data['data']
        self.msg_type = msg_type
        types = ['image', 'voice', 'video', 'link']
        if msg_type in types:
          self.msg_data = msg_data['url']
        elif msg_type == 'text':
          self.msg_data = msg_data['text']

        self._attr_native_value = now().replace(tzinfo=get_default_time_zone())
        self.update_attributes()
        self.schedule_update_ha_state()

    def update_attributes(self):
        self._attr_extra_state_attributes = {
          'msg_type': self.msg_type,
          'msg_data': self.msg_data
        }