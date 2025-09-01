import paho.mqtt.client as mqtt
import json, time, datetime, logging, re, asyncio, uuid
from urllib.parse import urlparse
from homeassistant.core import CoreState
from homeassistant.const import __version__ as current_version
from homeassistant.const import (
    EVENT_HOMEASSISTANT_STARTED
)

from .manifest import manifest
from .mqtt_user import MqttUser
from .event import EventEmit
from .assist import async_assistant 

_LOGGER = logging.getLogger(__name__)

class HaMqtt(EventEmit):

    def __init__(self, hass):
        super().__init__()
        self.host = 'mqtt://wecom:wecom@jiluxinqing.com:1883'
        self.hass = hass
        self.users = {}
        self.is_connected = False

        if hass.state == CoreState.running:
            self.connect()
        else:
            hass.bus.listen_once(EVENT_HOMEASSISTANT_STARTED, self.connect)

    def connect(self, event=None):

        HOST = self.host
        PORT = 1883
        client = mqtt.Client()        
        self.client = client

        if HOST.startswith("mqtt://"):
            parsed_url = urlparse(HOST)
            HOST = parsed_url.hostname
            PORT = parsed_url.port
            client.username_pw_set(parsed_url.username, parsed_url.password)

        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.on_subscribe = self.on_subscribe
        client.on_disconnect = self.on_disconnect
        client.connect(HOST, PORT, 60)
        client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        for topic in self.users:
            client.subscribe(topic)
        self.is_connected = True

    def close(self):
        self.client.disconnect()

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = str(msg.payload.decode('utf-8'))
        try:
            # 解析消息
            message = self.users[topic].get_message(payload)
            _LOGGER.debug(message)
            if message is not None and isinstance(message, dict):
                # 消息处理
                self.hass.create_task(self.async_handle_message(topic, message))
        except Exception as ex:
            print(ex)

    def on_subscribe(self, client, userdata, mid, granted_qos):
        print("【ha_mqtt】On Subscribed: qos = %d" % granted_qos)

    def on_disconnect(self, client, userdata, rc):
        print("【ha_mqtt】Unexpected disconnection %s" % rc)
        self.is_connected = False

    def publish(self, topic, payload):
        # 判断当前连接状态
        if self.client._state == 2:
            _LOGGER.debug('断开重连')
            self.client.reconnect()
            self.client.loop_start()
        self.client.publish(topic, payload, qos=1)

    def publish_server(self, topic, msg_type, msg_data):
        payload = self.get_user(topic).get_payload({
                'id': str(uuid.uuid4()),
                'time': int(time.time()),
                'type': msg_type,
                'data': msg_data
            })
        self.publish(f'ha_wecom/{topic}', payload)

    async def register(self, topic, key):
        self.users[topic] = MqttUser(topic, key)
        if self.is_connected:
            self.client.subscribe(topic, 2)

    def remove(self, topic):
        self.client.unsubscribe(topic)
        if topic in self.users:
            del self.users[topic]
        _LOGGER.debug(f'移除订阅 {topic}')

    def get_user(self, topic) -> MqttUser:
        return self.users.get(topic)

    async def async_handle_message(self, topic, data):
        msg_id = data['id']
        msg_topic = data['topic']
        msg_type = data['type']
        user = self.get_user(topic)
        result = await self.async_handle_data(user, data)

        if result is not None:
            # 加密消息
            payload = user.get_payload({
                'id': msg_id,
                'time': int(time.time()),
                'type': msg_type,
                'data': result
            })
            self.publish(msg_topic, payload)

        self.emit(f'{topic}message', data)

    async def async_handle_data(self, user, data):
        ''' 数据处理 '''
        _LOGGER.debug(data)
        hass = self.hass
        msg_type = data['type']
        msg_data = data['data']

        if msg_type == 'join':
            # 加入提醒
            user.join_result = msg_data
            user.join_event.set()
            return {
                'ha_version': current_version,
                'version': manifest.version
            }
        elif msg_type == 'enter_agent':
            return { 'speech': 'ok' }
        elif msg_type == 'image':
            self.emit(f'{user.topic}image', {
              'url': msg_data['url']
            })
            return { 'speech': 'HA已成功接收图片' }
        elif msg_type == 'voice':
            self.emit(f'{user.topic}voice', {
              'url': msg_data['url']
            })
            return { 'speech': 'HA已成功接收语音' }
        elif msg_type == 'video':
            self.emit(f'{user.topic}video', {
              'url': msg_data['url']
            })
            return { 'speech': 'HA已成功接收视频' }
        elif msg_type == 'link':
            self.emit(f'{user.topic}link', {
              'url': msg_data['url']
            })
            return { 'speech': 'HA已成功接收链接' }
        elif msg_type == 'location':
            self.emit(f'{user.topic}location', {
              'latitude': float(msg_data['latitude']),
              'longitude': float(msg_data['longitude']),
              'precision': float(msg_data['precision'])
            })
            return { 'speech': '定位成功' }
        elif msg_type == 'text':
            text = msg_data['text']
            result = await async_assistant(hass, text)
            if result is not None:
                return { 'speech': result }
        elif msg_type == 'conversation':
            text = msg_data['text']
            result = await async_assistant(hass, text)
            if result is not None:
                return { 'speech': result }

    async def waiting_join(self, topic):
        ''' 等待关联 '''
        user = self.get_user(topic)
        while True:
            if user.join_event.is_set():
                break
            else:
                await asyncio.sleep(1)
        return user.join_result

    def cancel_join(self, topic):
        ''' 取消关联 '''
        user = self.get_user(topic)
        if user is not None:
            user.join_result = None
            user.join_event.set()
            self.remove(topic)

    def call_service(self, service, data={}):
      arr = service.split('.')
      self.hass.async_create_task(self.hass.services.async_call(arr[0], arr[1], data))


async def register_mqtt(hass, topic, key):
    ''' 注册mqtt服务 '''
    ha_mqtt = hass.data.get(manifest.domain)
    if ha_mqtt is None:
        ha_mqtt = await hass.async_add_executor_job(HaMqtt, hass)
        hass.data[manifest.domain] = ha_mqtt
    await ha_mqtt.register(topic, key)
    return ha_mqtt