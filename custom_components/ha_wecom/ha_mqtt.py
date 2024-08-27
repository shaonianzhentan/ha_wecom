import paho.mqtt.client as mqtt
import json, time, datetime, logging, re, asyncio, uuid

from homeassistant.components.conversation.agent_manager import async_converse
from homeassistant.core import CoreState, Context
from homeassistant.const import __version__ as current_version
from homeassistant.const import (
    EVENT_HOMEASSISTANT_STARTED
)

from .EncryptHelper import EncryptHelper
from .manifest import manifest

_LOGGER = logging.getLogger(__name__)

class MqttUser():

    def __init__(self, key):
        self.key = key
        self.msg_cache = {}
        self.msg_time = None
        self.join_event = asyncio.Event()
        self.join_result = None

    @property
    def encryptor(self):
        return EncryptHelper(self.key, time.strftime('%Y-%m-%d', time.localtime()))

    # 清理缓存消息
    def clear_cache_msg(self):
        now = int(time.time())
        for key in list(self.msg_cache.keys()):
            # 缓存消息超过10秒
            if key in self.msg_cache and now - 10 > self.msg_cache[key]:
                del self.msg_cache[key]

    def get_message(self, data):
        data = json.loads(self.encryptor.Decrypt(data))
        _LOGGER.debug(data)
        self.clear_cache_msg()

        #self.msg_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())        
        now = int(time.time())
        # 判断消息是否过期(5s)
        if now - 5 > data['time']:
            print('【ha-mqtt】消息已过期')
            return

        msg_id = data['id']
        # 判断消息是否已接收
        if msg_id in self.msg_cache:
            print('【ha-mqtt】消息已处理')
            return

        # 设置消息为已接收
        self.msg_cache[msg_id] = now
        self.msg_time = datetime.datetime.now()

        return data

    def get_payload(self, data):
        return self.encryptor.Encrypt(json.dumps(data, cls=CJsonEncoder))

class HaMqtt():

    def __init__(self, hass):
        self.hass = hass
        self.users = {}
        self.is_connected = False

        if hass.state == CoreState.running:
            self.connect()
        else:
            hass.bus.listen_once(EVENT_HOMEASSISTANT_STARTED, self.connect)

    def connect(self, event=None):
        HOST = 'test.mosquitto.org'
        PORT = 1883
        client = mqtt.Client()        
        self.client = client
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
            print(message)
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
        print(topic, payload)
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
        self.users[topic] = MqttUser(key)
        if self.is_connected:
            self.client.subscribe(topic, 2)

    async def remove(self, topic):
        del self.users[topic]
        self.client.unsubscribe(topic)

    def get_user(self, topic) -> MqttUser:
        return self.users[topic]

    async def async_handle_message(self, topic, data):
        print(data)
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

    async def async_handle_data(self, user, data):
        ''' 数据处理 '''
        _LOGGER.debug(data)
        hass = self.hass
        msg_type = data['type']
        msg_data = data['data']

        body = msg_data.get('data', {})

        if msg_type == 'join':
            # 加入提醒
            user.join_result = msg_data
            user.join_event.set()
            return {
                'ha_version': current_version,
                'version': manifest.version
            }

        elif msg_type == 'conversation':
            text = msg_data['text']

            pipeline_data = hass.data['assist_pipeline']
            storage_collection = pipeline_data.pipeline_store
            pipelines = storage_collection.async_items()
            preferred_pipeline = storage_collection.async_get_preferred_item()

            for pipeline in pipelines:
              if pipeline.id == preferred_pipeline:
                conversation_result = await async_converse(
                    hass=hass,
                    text=text,
                    context=Context(),
                    conversation_id=None,
                    device_id=None,
                    language=hass.config.language,
                    agent_id=pipeline.conversation_engine,
                )
                intent_response = conversation_result.response
                speech = intent_response.speech.get('plain')
                if speech is not None:
                    result = speech.get('speech')
                    return { 'speech': result }

    async def waiting_join(self, topic):
        user = self.get_user(topic)
        while True:
            if user.join_event.is_set():
                break
            else:
                await asyncio.sleep(1)
        return user.join_result

    def call_service(self, service, data={}):
      arr = service.split('.')
      self.hass.async_create_task(self.hass.services.async_call(arr[0], arr[1], data))

class CJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)

async def register_mqtt(hass, topic, key):
    ''' 注册mqtt服务 '''
    ha_mqtt = hass.data.get(manifest.domain)
    if ha_mqtt is None:
        ha_mqtt = await hass.async_add_executor_job(HaMqtt, hass)
        hass.data[manifest.domain] = ha_mqtt
    await ha_mqtt.register(topic, key)
    return ha_mqtt