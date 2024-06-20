from celery import Celery

trumodity_app = Celery(
    'trumodity',
    include=['worker.trumodity.tasks']
)
trumodity_app.config_from_object('worker.trumodity.celery_config')
