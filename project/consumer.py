import json
import pika
import time

from app.models.settings import get_settings
from lib.celery_utils import send_msg_to_celery
from lib.logging import get_logger
from utils.constans import CONF_TRUMODITY

local_logger = get_logger(__name__)
config = get_settings()
credentials = pika.PlainCredentials(config.GC_RABBIT_USERNAME, config.GC_RABBIT_PASSWORD)
connection = pika.BlockingConnection(pika.ConnectionParameters(config.GC_RABBIT_HOST,
            config.GC_RABBIT_PORT,
            '/',
            credentials
))
channel = connection.channel()
channel.queue_declare(queue=config.GC_RABBIT_QUEUE)
local_logger.info(' [*] Waiting for messages')


def callback(ch, method, properties, body):
    try:
        local_logger.info(" [x] Queue Received %r" % body.decode())
        request = json.loads(body.decode())
        send_msg_to_celery([request], CONF_TRUMODITY)
        time.sleep(body.count(b'.'))
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as err:
        local_logger.error(f'Wrong message queue: {err}')


channel.queue_declare(queue=config.GC_RABBIT_QUEUE, durable=False)
channel.queue_bind(
    queue=config.GC_RABBIT_QUEUE,
    exchange=config.GC_RABBIT_EXCHANGE,
    routing_key=config.GC_RABBIT_ROUTING_KEY
)
channel.basic_qos(prefetch_count=1)
channel.basic_consume(
    queue=config.GC_RABBIT_QUEUE,
    on_message_callback=callback
)
try:
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()
connection.close()
