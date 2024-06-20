import zc.lockfile

from datetime import datetime
from pymongo import MongoClient

from app.models.settings import get_settings
from lib.logging import get_logger
import lib.pendingactions.syncers.add_blocks_to_farm
import lib.pendingactions.syncers.create_federation_block
import lib.pendingactions.syncers.create_federation_farm
import lib.pendingactions.syncers.create_federation_producer_farm_block
import lib.pendingactions.syncers.create_federation_producer
import lib.pendingactions.syncers.delete_federation_block
import lib.pendingactions.syncers.delete_federation_farm
import lib.pendingactions.syncers.delete_federation_producer
import lib.pendingactions.syncers.remove_blocks_from_farm
import lib.pendingactions.syncers.syncer_a
import lib.pendingactions.syncers.syncer_b
import lib.pendingactions.syncers.syncer_c
import lib.pendingactions.syncers.settle_contract_to_trumodity
import lib.pendingactions.syncers.sync_users_to_cas
import lib.pendingactions.syncers.sync_federation_data
from lib.pendingactions.syncer import ObjectSyncer
from lib.pendingactions.pendingaction import PendingAction
from worker.pendingactions.celery import worker

config = get_settings()
local_logger = get_logger(__name__)

def _has_previous_pending_action_for_execution(actionName) -> bool:
    with MongoClient(config.MONGODB_URI) as connection:
        db = connection.worker_sync
        action=db.actions.find_one({'action': actionName})
        if action == None or not 'parent' in action or action['parent'] == '': return False
        action=db.actions.find_one({'_id': action['parent']})
        pendingaction=db.pendingactions.find_one({
            'action': action['action'],
            "consumed" : False}
        )
        if(pendingaction != None):
            return True
        return False


@worker.task
def consume_pending_actions(action: str = None, request_payload: any = None):
    with MongoClient(config.MONGODB_URI) as connection:
        db = connection.worker_sync
        if not action is None:
            if action == "settle_contract_to_trumodity":
                counter = db.pendingactions.count_documents({'request_payload.purchase_order_id': request_payload['purchase_order_id']})
                if(counter > 0):
                    local_logger.error("Pending action with that purchase order has been previously processed.")
                    return True
            pendingaction = {
                'action': action,
                'request_payload': request_payload,
                'received': datetime.now(),
                'consumed': False
            }
            db["pendingactions"].insert_one(pendingaction)
        # Executing Syncers
        try:
            lock = zc.lockfile.LockFile('/tmp/consume-pending-actions.lock')
            syncer = ObjectSyncer()
            completed = True
            while completed:
                pendingactions = db.pendingactions.find({"consumed": False}).sort([("received", 1)])
                pending = False if pendingactions.count() > 0 else True
                for item in pendingactions:
                    pendingaction = PendingAction(item)
                    pending = _has_previous_pending_action_for_execution(item['action'])
                    if not pending:
                        try:
                            syncer.sync(pendingaction, item['action'])
                            local_logger.info(
                                f"--- Executed pending actions ({item['action']}) ---")
                            executedItem = db["pendingactions"].find_one({'_id': item['_id']})
                            local_logger.info(executedItem)
                        except Exception as e:
                            local_logger.error(e)
                            db.pendingactions.update_one(
                                {"_id":item['_id']}, {
                                    '$set': {
                                        "consumed": True,
                                        "successful": False,
                                        "response_payload": {}
                                    }
                                }
                            )
                if pending: completed = False
            lock.close()
            local_logger.info("--- Execution completed ---")
        except zc.lockfile.LockError:
           local_logger.error("--- Another process is executing the pending actions ---")
        except Exception as err:
            lock.close()
            if 'pendingactions' in locals() and pendingactions:
                local_logger.error(f"Pending action found: {list(pendingactions)}")
            if 'item' in locals() and item:
                local_logger.error(f"Current pending: {item}")
            local_logger.error(f"Error executing pending actions: {err}")
        return True
