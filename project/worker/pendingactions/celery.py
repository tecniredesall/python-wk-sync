from celery import Celery

worker = Celery(
    'pendingactions',
    include=['worker.pendingactions.tasks']
)
worker.config_from_object('worker.pendingactions.celery_config')
