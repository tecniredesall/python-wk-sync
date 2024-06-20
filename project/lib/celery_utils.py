import json
import os
import socket
import uuid

from kombu import Connection, Exchange, Producer, Queue

from app.models.settings import get_settings

def send_msg_to_celery(args, data):
    config = get_settings()
    task_id = str(uuid.uuid4())
    header2 = {
        'task': data["task"],
        'id': task_id,
        'origin': '@'.join([str(os.getpid()), socket.gethostname()])
    }
    conn = Connection(config.CELERY_BROKER_URL)
    channel = conn.channel()
    exchange = Exchange(data['exchange'], type=data['type_exchange'])
    producer = Producer(exchange=exchange, channel=channel, routing_key=data['routing_key'])
    queue = Queue(name=data['queue'], exchange=exchange, routing_key=data['routing_key'])
    queue.maybe_bind(conn)
    queue.declare()

    om = list()
    om.append(args)
    om.append({})
    om.append({})

    return producer.publish(json.dumps(om), headers=header2, **{
        'correlation_id': task_id,
        'content_type': 'application/json',
        'content_encoding': 'utf-8',
    })
