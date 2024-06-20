from app.models.settings import get_settings
from consumer_sqs import ConsumerSQS
from lib.logging import get_logger
from lib.celery_utils import send_msg_to_celery
from utils.constans import CONF_PENDING
from worker.federation.celery import federation_app
from worker.tasks.base import Task

config = get_settings()
local_logger = get_logger(__name__)


@federation_app.task(bind=True, base=Task)
def get_updates_federation(self):
    try:
        conf = {
            "QUEUE_URL": (config.AWS_QUEUE_URL_FEDERATION + config.AWS_QUEUE_NAME_FEDERATION),
            "AWS_REGION_FEDERATION": config.AWS_REGION_FEDERATION,
            "AWS_ACCESS_KEY_FEDERATION": config.AWS_ACCESS_KEY_FEDERATION,
            "AWS_SECRET_FEDERATION": config.AWS_SECRET_FEDERATION
        }
        is_updated = False
        messages = ConsumerSQS(conf).receive_messages()
        for message in messages:
            if "platform" in message and message["platform"] != config.CODE_PLATFORM:
                is_updated = True
                break
        if is_updated:
            args = ["sync-federation-data",{}]
            send_msg_to_celery(args, CONF_PENDING)
    except Exception as err:
        local_logger.error(f'An error occurred while getting messages from federation sqs: {err}')
