from celery import Celery

federation_app = Celery(
    'federation',
    include=['worker.federation.tasks']
)
federation_app.config_from_object('worker.federation.celery_config')
