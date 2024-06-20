import json
import zc.lockfile

from bson.objectid import ObjectId
from typing import List
from fastapi import status
from pymongo import MongoClient

from app.models.settings import get_settings
from lib.logging import get_logger 
from lib.pendingactions.syncer import Syncer
from lib.pendingactions.syncer import factory
from utils.api import API
from utils.constans import APP_FEDERATION
from utils.pendingactions import Pendingactions
from app.queries.blocks import query_blocks_by_farm_and_code

local_logger = get_logger(__name__)
config = get_settings()


class RemoveBlocksFromFarm(Syncer):
    def __init__(self):
        Syncer.__init__(self)
        self._received = None


    def get_access(self):
        pass


    def remove_blocks_from_farm(self, data):
        with MongoClient(config.MONGODB_URI) as connection:
            db = connection.federation
            pipe = query_blocks_by_farm_and_code(data["federated_farm"])
            blocks = db.farm.aggregate(pipe)
            blocks = blocks.next()
        if blocks and "blocks" in blocks and blocks["blocks"]:
            path = f'/producers/{data["federated_produce"]}/farms/{data["federated_farm"]}'
            blocks = [str(item["_id"]) for item in blocks["blocks"]]
            payload = {
                "blocks": blocks,
                "source_type": "farm",
                "destination_type": "producer"
            }
            result = API(APP_FEDERATION).patch(path, json.dumps(payload))
            if result["status"] == status.HTTP_200_OK:
                return {
                    "success": True,
                    "data": {"status": status.HTTP_200_OK, "message": f'The blocks {blocks} were correctly related with producer.'}
                }
            else:
                return {
                    "success": False,
                    "data": {"status": status.HTTP_200_OK, "message": f'Error: {result["data"]}, the blocks {blocks} could not be made.'}
                }
        message = f'No blocks found in the farm {data["federated_farm"]}.'
        return {
            "success": True,
            "data": {"status": status.HTTP_200_OK, "message": message}
        }


    def get_producer_federated_id(self, federated_farm):
        with MongoClient(config.MONGODB_URI) as connection:
            db = connection.federation
            data = db.producer.find_one(
                {'farms': ObjectId(federated_farm)}, {"_id": 1}
            )
            if data and "_id" in data and data["_id"]:
                return str(data["_id"])
        return None


    def send_add_blocks_to_farm(self, data, blocks):
        action = "add-blocks-to-farm"
        payload = {
            "blocks": blocks,
            "federated_produce": data["federated_produce"],
            "federated_farm": data["federated_farm"]
        }
        response = Pendingactions().create_pendingactions(action, payload, self._received)
        if response:
            return {"status": True, "message": "Create pendingactions to add blocks to farm."}
        else:
           return {"status": False, "message": "Couldn't create pendingactions to add blocks to farm."}


    def send_create_federation_blocks(self, blocks):
        action = "create-federation-block"
        payload = {"items": blocks}
        response = Pendingactions().create_pendingactions(action, payload, self._received)
        if response:
            return {"status": True, "message": "Create pendingactions to create federation block."}
        else:
            return {"status": False, "message": "Couldn't create pendingactions to create federation block."}


    def organization_and_send_blocks(self, data):
        add_blocks = {}
        create_blocks = {}
        blocks = data["blocks"] if "blocks" in data else None
        object_blocks = []
        blocks_id = []
        success = True
        error = None
        if blocks:
            blocks = self.block_verification(blocks)
            blocks_id = blocks["federated"]
            object_blocks = blocks["not_federated"]
            success = blocks["success"]
            error = blocks["message"]
        if blocks_id:
            add_blocks = self.send_add_blocks_to_farm(data, blocks_id)
            if not add_blocks["status"]:
                success = False
        else:
            add_blocks = {"status": True, "message": "No new blocks were sent to relate to a farm."}
        if object_blocks:
            create_blocks = self.send_create_federation_blocks(object_blocks)
            if not create_blocks["status"]:
                success = False
        else:
            create_blocks = {"status": True, "message": "No new blocks were sent to create in federation."}
        return {
            "success": success,
            "add_blocks": add_blocks,
            "create_blocks": create_blocks,
            "error": error
        }


    def block_verification(self, blocks):
        blocks_federated = []
        blocks_not_federated = []
        success = True
        messages = []
        for block in blocks:
            with MongoClient(config.MONGODB_URI) as connection:
                db = connection.federation
                data = db.block.find_one({
                    "$and": [
                        {"platforms.code": config.CODE_PLATFORM},
                        {"platforms.idBlock":  block["id"]}
                    ]
                })
                if data and "_id" in data and data["_id"]:
                    federated_id = str(data["_id"])
                    duplicate = False
                    if("federated_id" in block and block["federated_id"] and block["federated_id"] != federated_id):
                        message = f'The block {block["id"]} was send with federation id {block["federated_id"]} is not the same as the one found in mongo {federated_id}.'
                        messages.append(message)
                        success = False
                        duplicate = True
                        local_logger.error(message)
                    if not duplicate:
                        blocks_federated.append(federated_id)
                else:
                    blocks_not_federated.append(block)
        return {
            "federated": blocks_federated,
            "not_federated": blocks_not_federated,
            "success": success,
            "message": messages
        }


    def do_sync(self) -> List:
        success = True
        response_data = {}
        self._response_payload = {}
        consumed = True
        try:
            lock = zc.lockfile.LockFile('/tmp/flow-create-farm-block.lock')
            request_payload = self._request_payload['request_payload']
            self._received = self._request_payload['received']
            if "federated_farm" in request_payload and "blocks" in request_payload:
                request_payload["federated_produce"] = self.get_producer_federated_id(request_payload["federated_farm"])
                if request_payload["federated_produce"]:
                    response_data = self.remove_blocks_from_farm(request_payload)
                    success = response_data["success"]
                    self._response_payload = response_data["data"]
                    if success:
                        response_data = self.organization_and_send_blocks(request_payload)
                        success = response_data["success"]
                        if response_data["error"]:
                            self._response_payload["error"] = response_data["error"]
                        self._response_payload["add_blocks"] = response_data["add_blocks"]
                        self._response_payload["create_blocks"] = response_data["create_blocks"]
                else:
                    success = False
                    message = "Could not get the producer id of the farm {request_payload['federated_farm']}."
                    self._response_payload = {"message": message}
            else:
                success = False
                message = "The data id farm of federation or the list of blocks have to be sent."
                self._response_payload = {"message": message }
            lock.close()
        except zc.lockfile.LockError:
            consumed = False
            message = "Another farm / block creation process is running."
            self._response_payload = {"message": message}
            local_logger.info(message)
            success = False
        except Exception as err:
            success = False
            local_logger.error(f"Error executing remove-blocks-from-farm: {err}")
            lock.close()
        self.update_task(success, consumed)
        local_logger.info("[x] Sent")
        return True


factory.register_task('remove-blocks-from-farm', RemoveBlocksFromFarm)
