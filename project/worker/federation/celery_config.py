from kombu import Queue, Exchange

from app.models.settings import get_settings
from utils.constans import CONF_FEDERATION

config = get_settings()

broker_url = config.CELERY_BROKER_URL
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Europe/Dublin'
enable_utc = True

task_default_queue = CONF_FEDERATION['queue']
task_default_exchange_type = CONF_FEDERATION['type_exchange']
task_default_exchange = Exchange(CONF_FEDERATION['exchange'], type=task_default_exchange_type)
task_create_missing_queues = False
task_default_routing_key = CONF_FEDERATION['routing_key']
task_queues = [
    Queue(task_default_queue, task_default_exchange,
          routing_key=task_default_routing_key),
]
task_routes = {
    'worker.federation.tasks.*': {'queue': task_default_queue, 'routing_key': task_default_routing_key},
}
