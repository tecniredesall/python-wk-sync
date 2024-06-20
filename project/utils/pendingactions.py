from datetime import datetime
from pymongo import MongoClient

from app.models.settings import get_settings
from lib.logging import get_logger

local_logger = get_logger(__name__)
config = get_settings()

class Pendingactions:

    def create_pendingactions(self, action, data, date = None):
        if not date:
            date = datetime.now()
        with MongoClient(config.MONGODB_URI) as connection:
            db = connection.worker_sync
            actionCounter = db.actions.count_documents({
                "action": action,
                "active": False
            })
            if actionCounter == 0:
                pendingaction = {
                    'action': action,
                    'request_payload': data,
                    'received': date,
                    'consumed': False
                }
                db.pendingactions.insert_one(pendingaction)
                return True
        local_logger.error("Error: Could not create pending action {action}.")
        return False


    def verify_pendingaction(self, action):
        with MongoClient(config.MONGODB_URI) as connection:
            db = connection.worker_sync
            pendingactionCounter = db.pendingactions.count_documents({
                "action": action,
                "consumed": False
            })
            if pendingactionCounter > 0:
                return True
            return False


    def sync_federation_data(self, date= datetime.now()):
        action = "sync-federation-data"
        payload = {}
        exist_pending = self.verify_pendingaction(action)
        if exist_pending:
            return {"status": True, "message": "There is a pending action to synchronize data from federation to be executed."}
        else:
            response = self.create_pendingactions(action, payload, date)
        if response:
            return {"status": True, "message": "Create pendingaction sync federation data."}
        else:
            return {"status": False, "message": "Couldn't create pendingactions sync federation data."}
