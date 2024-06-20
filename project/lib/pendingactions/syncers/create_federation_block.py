import zc.lockfile

from fastapi import status
from typing import List

from app.models.settings import get_settings
from lib.logging import get_logger
from lib.pendingactions.syncer import Syncer
from lib.pendingactions.syncer import factory
from utils.api import API
from utils.constans import (
    APP_FEDERATION,
    APP_TRANSFORMATIONS
)
from utils.pendingactions import Pendingactions

local_logger = get_logger(__name__)
config = get_settings()


class CreateFederationBlock(Syncer):

    def get_access(self):
        pass

    #Register the federation id directly in the block table in the transformation database.
    def record_data_transformations(self, data):
        success = True
        message = ""
        if data["federated_block"]:
            if data["federated_block"] != data["federated_id"]:
                message = f'Transformation table block: The block with the id {data["block_id"]} has the federation id {data["federated_id"]} different from the one registered in the transformations with the id {data["federated_block"]}'
                local_logger.error(message)
                success = False
            else:
                message = f'Transformation table block: the federation id was previously registered.'
        else:
            payload = {
                "federated": data["federated_id"]
            }
            path = f'/web/federation/blocks/{data["block_id"]}'
            response = API(APP_TRANSFORMATIONS).patch(path, payload)
            if not response["data"]:
                message = "Error while trying to update the block."
            else:
                message = response["data"]["message"]
        return {
            "success": success,
            "message": message
        }


    #Collation of information and structure of the information received.
    def information_processing(self, block_data):
        return {
            "idFederated": block_data["federated_id"] if "federated_id" in block_data and block_data["federated_id"] else None,
            "name": block_data["name"],
            "parsedAddress": block_data["address"] if "address" in block_data and block_data["address"] else None,
            "extension": block_data["extension_block"] if "extension_block" in block_data and  block_data["extension_block"] else None,
            "_partitionKey": config.PARTITION_KEY,
            "platform": {
                "code": config.CODE_PLATFORM,
                "idProducer": block_data["seller"],
                "idFarm": block_data["farm"] if "farm" in block_data and  block_data["farm"] else None,
                "idBlock": block_data["id"]
            },
            "latitude": block_data["latitude"] if "latitude" in block_data and block_data["latitude"] else None,
            "longitude": block_data["longitude"] if "longitude" in block_data and block_data["longitude"] else None,
            "unitExtension": block_data["unit_extension"] if "unit_extension" in block_data and block_data["unit_extension"] else None,
            "msl": block_data["height"] if "height" in block_data and block_data["height"] else None,
            "extras": block_data["extras"] if "extras" in block_data and block_data["extras"] else None
        }


    #verify that the record exists in transformations and get federated_id
    def get_federation_transformations(self, block_id):
        path = f'/web/federation/blocks/{block_id}'
        farm_data = API(APP_TRANSFORMATIONS).get(path)
        federated_id = farm_data["data"]
        if "data" in federated_id and "federated" in federated_id["data"]:
            return federated_id["data"]["federated"]
        else:
            return {
                "success": False,
                "message": f'Transformations response: {federated_id["message"]}'
            }


    #Send pending action for create producer/farm
    def create_federation_producer_farm_block(self, payload):
        action = "create-federation-producer-farm-block"
        response = Pendingactions().create_pendingactions(action, payload)
        if response:
            return "Create pendingactions to create producer/farm."
        else:
            return "Couldn't create pendingactions to create producer/farm."


    #Create/update a new federation registration by consuming an endpoint.
    def send_data_fedration(self, payload):
        path = "/blocks"
        response_orphan = None
        response_data = None
        response = API(APP_FEDERATION).post(path, payload)
        if response["status"] == status.HTTP_200_OK:
            if "isOrphan" in response["data"] and response["data"]["isOrphan"]:
                orphan_payload = {"items": [
                    {
                        "producer": payload["platform"]["idProducer"],
                        "block": payload["platform"]["idBlock"],
                        "farm": payload["platform"]["idFarm"] if "idFarm" in payload["platform"] and payload["platform"]["idFarm"] else None
                    }
                ]}
                response_orphan = self.create_federation_producer_farm_block(orphan_payload)
            else:
                return {
                    "success": True,
                    "data": response["data"]
                }
        response_data = {
            "success": False,
            "response": {
                "message":   f'Federation response ({response["status"]}): {response["data"]}',
                "data_sent": payload
            }
        }
        if response_orphan:
            response_data["create_producer"] = response_orphan
        return response_data


    def do_sync(self) -> List:
        success = True
        response_data_list = []
        consumed = True
        try:
            lock = zc.lockfile.LockFile('/tmp/flow-create-farm-block.lock')
            items = self._request_payload['request_payload']['items']
            for data in items:
                federated_block = self.get_federation_transformations(data["id"])
                response_data = {}
                if type(federated_block) != dict:
                    if (not ("federated_id" in data and data["federated_id"])) and federated_block:
                        data["federated_id"] = federated_block
                    block_data = self.information_processing(data)
                    response_data = self.send_data_fedration(block_data)
                    if response_data["success"]:
                        response_data["data"] = {
                            "block_id": data["id"],
                            "federated_id": response_data["data"]["id"],
                            "federated_block":  federated_block
                        }
                        record_data = self.record_data_transformations(response_data["data"])
                        response_data["message"] = record_data["message"]
                        success = record_data["success"]
                    else:
                        success = False
                else:
                    response_data["message"] = federated_block["message"]
                    success = federated_block["success"]
                response_data_list.append(response_data)
            if success:
                sync_federation = Pendingactions().sync_federation_data()
                response_data["sync_federation"] = sync_federation
            self._response_payload = response_data_list
            lock.close()
        except zc.lockfile.LockError:
            consumed = False
            message = "Another farm / block creation process is running."
            self._response_payload = {"message": message}
            local_logger.info(message)
            success = False
        except Exception as err:
            success = False
            if 'data' in locals() and data:
                local_logger.error(f"Current item: {data}")
            local_logger.error(f"Error executing create-federation-block: {err}")
            lock.close()
        self.update_task(success, consumed)
        local_logger.info("[x] Sent")
        return True


factory.register_task('create-federation-block', CreateFederationBlock)
