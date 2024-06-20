from pymongo import MongoClient

from app.models.settings import get_settings

config = get_settings()

def record_count(action):
    with MongoClient(config.MONGODB_URI) as connection:
        db = connection.worker_sync
        return db.pendingactions.count_documents({'action': action})


def get_last_record(action):
    with MongoClient(config.MONGODB_URI) as connection:
        db = connection.worker_sync
        record = db.pendingactions.find(
            {'action': action}).sort('$natural', -1).limit(1)
        if record:
            record = str(record[0]['_id'])
        return record
