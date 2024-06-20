import celery

from app.models.settings import get_settings

class Task(celery.Task):
    def __call__(self, *args, **kwargs):
        self.config = get_settings()
        return super().__call__(*args, **kwargs)
