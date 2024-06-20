from datetime import datetime
from pymongo import MongoClient

from app.models.settings import get_settings
from lib.pendingactions.syncer import Syncer, factory
from lib.logging import get_logger
from lib.trumodity import TrumodityHandler

local_logger = get_logger(__name__)

class SettleContractToTrumodity(Syncer):

    def get_access(self):
        pass


    def do_sync(self):
        try:
            config = get_settings()
            success = True
            message = self._request_payload['request_payload']
            response_payload = "purchase order processed"
            if 'purchase_order_id' in message:
                with MongoClient(config.MONGODB_URI) as connection:
                    db = connection.worker_sync
                    counter = db.settling_processes.count_documents(
                        {"$and":[
                            {'purchase_order_id': message['purchase_order_id']},
                            {"$or":[
                                {"removed": {"$exists": False}},
                                {"removed": False}
                            ]}
                        ]}
                    )
                    if(counter == 0):
                        db.settling_processes.insert_one({
                            'purchase_order_id': message['purchase_order_id'],
                            'status': None,
                            'received': datetime.now(),
                            'messages': list(),
                        })
                        inserted = db.settling_processes.find_one({"$and": [
                            {'purchase_order_id': message['purchase_order_id']},
                            {"$or": [
                                {"removed": {"$exists": False}},
                                {"removed": False}
                            ]}
                        ]})
                        message['id'] = str(inserted['_id'])
                        message['purchase_order_id'] = str(message['id'])
                        TrumodityHandler.send_settling_message(message)
                    else:
                        local_logger.error("Purchase order has already being settle")
                        response_payload = "Purchase order has already being settle"
                        success = False
            elif not 'purchase_order_id' in message:
                local_logger.error("Bad payload")
                response_payload = "Bad payload"
                success = False
            else:
                local_logger.error("Something went wrong with Rabbit")
                response_payload = "Something went wrong with Rabbit"
                success = False
        except Exception as err:
            success = False
            local_logger.error(f"Error executing settle_contract_to_trumodity: {err}")
            response_payload = f"Error executing settle_contract_to_trumodity: {err}"
        self._response_payload = response_payload
        self.update_task(success)
        return True

factory.register_task('settle_contract_to_trumodity', SettleContractToTrumodity)
