import re
import time

from app.models.settings import get_settings
from celery import Celery
from dotenv import load_dotenv, find_dotenv
from lib.logging import get_logger
from pymongo import MongoClient

load_dotenv(find_dotenv())
local_logger = get_logger(__name__)
config = get_settings()

celery = Celery(__name__)
celery.conf.broker_url = config.CELERY_BROKER_URL
celery.conf.result_backend = config.CELERY_RESULT_BACKEND
celery.autodiscover_tasks(['worker.trumodity', 'worker.pendingactions', 'worker.federation'], force=True)

celery.conf.beat_schedule = {
    'get-updates-federation': {
        'task': 'worker.federation.tasks.get_updates_federation',
        'schedule': config.GET_CHANGES_PLATFORMS_TIMER
    },
}

if config.GET_CONTRACTS:
    celery.conf.beat_schedule["get-contracts-from-trumodity"] = {
        "task": "worker.trumodity.tasks.get_trumodity_contracts",
        "schedule": config.GET_CONTRACTS_TIMER
    }
    celery.conf.beat_schedule["resend-message-for-settle"] = {
        "task": "worker.trumodity.tasks.resend_message_for_settle",
        "schedule": config.RESEND_MESSAGE_TIMER
    }

with MongoClient(config.MONGODB_URI) as connection:
    db = connection.worker_sync
    actions = db.actions.find({
    'active': True,
    'schedule': {'$exists': True}
})

for action in actions:
    celery.conf.beat_schedule[f"periodic-pending-action-{action['action']}"] = {
        'task': 'worker.pendingactions.tasks.consume_pending_actions',
        'schedule': float(action['schedule']) if re.match(r'^(\d)+(\.(\d)+)?$', action['schedule']) else eval(action['schedule']),
        'args': [action['action'], action['payload'] if 'payload' in action else {}]
    }


@celery.task(name="create_task")
def create_task(task_type):
    local_logger.info('--------------- Testing task ---------------------')
    time.sleep(int(task_type) * 10)
    return True



