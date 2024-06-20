import os
import uuid
import pika
import json

import numpy as np
from faker import Faker

from datetime import datetime
from pymongo import MongoClient

from app.models.settings import get_settings
from worker.trumodity.celery import trumodity_app

def test_migrate_contracts():
    if os.path.exists("/tmp/sync-trumodity-contracts.lock"):
        assert trumodity_app.send_task("worker.trumodity.tasks.get_trumodity_contracts", args=[])
    else:
        return True

def test_resend_message_for_settle():
    config = get_settings()
    with MongoClient(config.MONGODB_URI) as connection:
        db = connection.worker_sync
        counter = db.settling_processes.count_documents({'status': None})
        if(counter == 0):
            purchase_order_id = str(uuid.uuid4())
            pendingaction = {
                'action': "settle_contract_to_trumodity",
                'request_payload': {
                    "purchase_order_id": purchase_order_id,
                    "contract_id":"D00001",
                    "totalAmount":1.0339454,
                    "loads":[
                        {
                            "weight":999999.990,
                            "characteristics":{
                            "type":"adjust",
                            "value":100.000,
                            "originalValue":0.20,
                            "difference":0.000,
                            "total":99999999.000000
                            }
                        }
                    ]
                },
                'received': datetime.now(),
                'consumed': False
            }
            db.pendingactions.insert_one(pendingaction)
            db.settling_processes.insert_one({
                'purchase_order_id': purchase_order_id,
                'received': datetime.now(),
                'status': None,
            })
    assert trumodity_app.send_task("worker.trumodity.tasks.resend_message_for_settle", args=[])


def test_change_settling_status():
    config = get_settings()
    fake = Faker()
    with MongoClient(config.MONGODB_URI) as connection:
        db = connection.worker_sync
        counter = db.settling_processes.count_documents({'status': None,})
        if(counter == 0):
            purchase_order_id = str(uuid.uuid4())
            db.settling_processes.insert_one({
                'purchase_order_id': purchase_order_id,
                'received': datetime.now(),
                'status': None,
            })
        item = db.settling_processes.find_one({'status': None})
        id = str(item['_id'])
        
        # Sending queue
        message = json.dumps({"process_id": id, "status": np.random.choice(['received', 'read', 'settled'])})
        credentials = pika.PlainCredentials(config.GC_RABBIT_USERNAME, config.GC_RABBIT_PASSWORD)
        connection = pika.BlockingConnection(pika.ConnectionParameters(config.GC_RABBIT_HOST,
                    config.GC_RABBIT_PORT,
                    '/',
                    credentials
        ))
        channel = connection.channel()
        channel.queue_declare(queue=config.GC_RABBIT_QUEUE)
        channel.queue_bind(
            queue=config.GC_RABBIT_QUEUE,
            exchange=config.GC_RABBIT_EXCHANGE,
            routing_key=config.GC_RABBIT_ROUTING_KEY
        )
        channel.basic_publish(
            exchange=config.GC_RABBIT_EXCHANGE,
            routing_key=config.GC_RABBIT_ROUTING_KEY,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode = 2, # make message persistent
            ))
        connection.close()
        assert True
