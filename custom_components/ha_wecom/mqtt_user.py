import logging, json, asyncio, time, datetime
from .EncryptHelper import EncryptHelper

_LOGGER = logging.getLogger(__name__)

class MqttUser():

    def __init__(self, topic, key):
        self.topic = topic
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

class CJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)