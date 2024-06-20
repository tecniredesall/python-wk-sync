from __future__ import annotations
from abc import ABC, abstractmethod
from bson.objectid import ObjectId
from datetime import datetime
from pymongo import MongoClient

from app.models.settings import get_settings

class Syncer(ABC):

    def __init__(self):
        self._id = None
        self._request_payload = None
        self._response_payload = None


    @abstractmethod
    def get_access(self):
        pass


    @abstractmethod
    def do_sync(self):
        pass


    def start_object(self, object_name, object_id):
        self._id = ObjectId(object_id)
        self._request_payload = dict()


    def add_property(self, name, value):
        self._request_payload[name] = value


    def update_task(self, success=True, consumed=True):
        config = get_settings()
        with MongoClient(config.MONGODB_URI) as connection:
            db = connection.worker_sync
            action = db.pendingactions.find_one({"_id": self._id }, { "action": 1})['action']
            actionCounter = db.actions.count_documents({'action': action})
            if(actionCounter == 0):
                db.actions.insert_one({
                    'action': action,
                    'active': True,
                    'created': datetime.now(),
                })
            db.pendingactions.update_one(
                {"_id": self._id }, {
                    '$set': {
                        "consumed": consumed,
                        "successful": success,
                        "response_payload": self._response_payload
                    }
                }
            )


class ObjectSyncer:
    def sync(self, synchronizable, task):
        syncer = factory.get_syncer(task)
        synchronizable.sync(syncer)
        syncer.get_access()
        return syncer.do_sync()


class SyncerFactory:

    def __init__(self):
        self._creators = {}


    def register_task(self, task, creator):
        self._creators[task] = creator


    def get_syncer(self, task):
        creator = self._creators.get(task)
        if not creator:
            raise ValueError(task)
        return creator()


factory = SyncerFactory()
