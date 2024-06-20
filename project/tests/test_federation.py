import datetime
import random
import time

from app.models.settings import get_settings
from consumer_sqs import SendMessageSQS
from utils.constans import CONF_FEDERATION
from tests.fuctions import record_count
from worker.federation.celery import federation_app


config = get_settings()


def _send_message_federation(messages):
    conf = {
        "QUEUE_URL": (config.AWS_QUEUE_URL_FEDERATION + config.AWS_QUEUE_NAME_FEDERATION),
        "AWS_REGION_FEDERATION": config.AWS_REGION_FEDERATION,
        "AWS_ACCESS_KEY_FEDERATION": config.AWS_ACCESS_KEY_FEDERATION,
        "AWS_SECRET_FEDERATION": config.AWS_SECRET_FEDERATION
    }
    return SendMessageSQS(conf).send_messages(messages)


def test_get_updates_federation():
    assert federation_app.send_task(CONF_FEDERATION['task'], args=[])


def test_send_variety_message_federation():
    loop = 60
    platform = ["silosys", "seed-audit", "tp-suma", "commodity-v1"]
    messages = []
    for i in range(loop):
        time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+%f')
        messages.append({
            "event": "notification.data-update",
            "timestamp": time,
            "platform": platform[random.randint(0, 3)],
            "secuencia": str(i)
        })
    assert _send_message_federation(messages)


def test_send_silosys_message_federation():
    messages = []
    loop = 60
    for i in range(loop):
        time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+%f')
        messages.append({
            "event": "notification.data-update",
            "timestamp": time,
            "platform": "silosys",
            "secuencia": str(i)
        })
    assert _send_message_federation(messages)


def test_send_and_get_message_federation():
    action = "sync-federation-data"
    total_records = record_count(action)
    test_send_variety_message_federation()
    time.sleep(2)
    test_get_updates_federation()
    time.sleep(2)
    current_records = record_count(action)
    assert current_records >= total_records


def test_send_and_get_silosys_message_federation():
    action = "sync-federation-data"
    total_records = record_count(action)
    test_send_silosys_message_federation()
    test_get_updates_federation()
    current_records = record_count(action)
    assert current_records == total_records
