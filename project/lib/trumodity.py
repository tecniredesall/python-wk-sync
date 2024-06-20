import threading

import json
import pika
import time

from app.models.settings import get_settings
from lib.logging import get_logger

local_logger = get_logger(__name__)
config = get_settings()

class TrumodityHandler():
    @staticmethod
    def send_settling_message(message):
        credentials = pika.PlainCredentials(config.GC_RABBIT_USERNAME, config.GC_RABBIT_PASSWORD)
        connection = pika.BlockingConnection(pika.ConnectionParameters(config.GC_RABBIT_HOST,
                    config.GC_RABBIT_PORT,
                    '/',
                    credentials
        ))
        channel = None
        if connection:
            channel = connection.channel()
        if channel:
            channel.queue_declare(queue='load', durable=True)
            channel.queue_bind(queue='load', exchange='cmodity', routing_key='load.*')
            channel.queue_bind(queue='load', exchange='cmodity', routing_key='load.*.*')
            channel.queue_bind(queue='load', exchange='cmodity', routing_key='load.trumodity_batch')
            channel.basic_publish(exchange='cmodity',
                routing_key='load.trumodity_batch',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode = 2, # make message persistent
                ))
            local_logger.info("[x] Sent message to queue load %r" % message)
            connection.close()


    @staticmethod
    def get_settling_status():
        credentials = pika.PlainCredentials(config.GC_RABBIT_USERNAME, config.GC_RABBIT_PASSWORD)
        connection = pika.BlockingConnection(pika.ConnectionParameters(config.GC_RABBIT_HOST,
                    config.GC_RABBIT_PORT,
                    '/',
                    credentials
        ))
        channel = None
        if connection:
            channel = connection.channel()
        if channel:
            def callback(ch, method, properties, body):
                local_logger.info(" [x] Received %r" % body.decode())
                time.sleep(body.count(b'.'))
                local_logger.info(" [x] Done")
                ch.basic_ack(delivery_tag=method.delivery_tag)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=config.GC_RABBIT_QUEUE, on_message_callback=callback)
            mq_recieve_thread = threading.Thread(target=channel.start_consuming)
            mq_recieve_thread.start()
