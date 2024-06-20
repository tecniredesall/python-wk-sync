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


class CreateFederationFarm(Syncer):
    def __init__(self):
        Syncer.__init__(self)
        self._received = None


    def get_access(self):
        pass


    #Register the federation id directly in the farm table in the transformation database.
    def record_data_transformations(self, data):
        success = True
        message = ""
        if data["federated_farm"]:
            if data["federated_farm"] != data["federated_id"]:
                message = f'Transformation table farm: The farm with the id {data["farm_id"]} has the federation id {data["federated_id"]} different from the one registered in the transformations with the id {data["federated_farm"]}'
                local_logger.error(message)
                success = False
            else:
                message = f'Transformation table farm: the federation id was previously registered.'
        else:
            payload = {
                "federated": data["federated_id"]
            }
            path = f'/web/federation/farms/{data["farm_id"]}'
            response = API(APP_TRANSFORMATIONS).patch(path, payload)
            if not response["data"]:
                message = "Error while trying to update the farm."
            else:
                message = response["data"]["message"]
        return {
            "success": success,
            "message": message
        }


    #Collation of information and structure of the information received.
    def information_processing_federation(self, farm_data):
        return {
            "idFederated": farm_data["federated_id"] if "federated_id" in farm_data and farm_data["federated_id"] else None,
            "name": farm_data["name"],
            "parsedAddress": farm_data["address"] if "address" in farm_data and farm_data["address"] else None,
            "extension": farm_data["extension"] if "extension" in farm_data and  farm_data["extension"] else None,
            "_partitionKey": config.PARTITION_KEY,
            "platform": {
                "code": config.CODE_PLATFORM,
                "idProducer": farm_data["seller"],
                "idFarm": farm_data["id"],
            },
            "latitude": farm_data["latitude"] if "latitude" in farm_data and farm_data["latitude"] else None,
            "longitude": farm_data["longitude"] if "longitude" in farm_data and farm_data["longitude"] else None,
            "unitExtension": farm_data["unit_extension"] if "unit_extension" in farm_data and farm_data["unit_extension"] else None,
            "msl": farm_data["msl"] if "msl" in farm_data and farm_data["msl"] else None,
            "extras": farm_data["extras"] if "extras" in farm_data and farm_data["extras"] else None
        }


    #verify that the record exists in transformations and get federated_id
    def get_federation_transformations(self, farm_id):
        path = f'/web/federation/farms/{farm_id}'
        farm_data = API(APP_TRANSFORMATIONS).get(path)
        federated_id = farm_data["data"]
        if "data" in federated_id and "federated" in federated_id["data"]:
            return federated_id["data"]["federated"]
        else:
            return {
                "success": False,
                "message":  f'Transformations response: {federated_id["message"]}'
            }


    #Send pending action for create producer
    def create_federation_producer_farm_block(self, payload):
        action = "create-federation-producer-farm-block"
        response = Pendingactions().create_pendingactions(action, payload, self._received)
        if response:
            return "Create pendingactions to create producer."
        else:
            return "Couldn't create pendingactions to create producer."


    #Create/update a new federation registration by consuming an endpoint.
    def send_data_federation(self, payload):
        path = "/farms"
        response_orphan = None
        response_data = None
        response = API(APP_FEDERATION).post(path, payload)
        if response["status"] == status.HTTP_200_OK:
            if "isOrphan" in response["data"] and response["data"]["isOrphan"]:
                orphan_payload = {"items":[{"producer": payload["platform"]["idProducer"], "farm": payload["platform"]["idFarm"]}]}
                response_orphan = self.create_federation_producer_farm_block(
                    orphan_payload)
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


    #Send pending action for remove blocks from farms
    def remove_blocks_from_farm(self, federated_farm, blocks):
        action = "remove-blocks-from-farm"
        payload = {
            "federated_farm": federated_farm,
            "blocks": blocks
        }
        response = Pendingactions().create_pendingactions(action, payload, self._received)
        if response:
            return {"status": True, "message": "Create pendingactions remove blocks from farm."}
        else:
            return {"status": False, "message": "Couldn't create pendingactions remove blocks from farm."}


    def do_sync(self) -> List:
        success = True
        response_data_list = []
        consumed = True
        try:
            lock = zc.lockfile.LockFile('/tmp/flow-create-farm-block.lock')
            items = self._request_payload['request_payload']['items']
            self._received = self._request_payload['received']
            for data in items:
                federated_farm = self.get_federation_transformations(data["id"])
                response_data = {}
                if type(federated_farm) != dict:
                    if (not ("federated_id" in data and data["federated_id"])) and federated_farm:
                        data["federated_id"] = federated_farm
                    farm_data = self.information_processing_federation(data)
                    response_data = self.send_data_federation(farm_data)
                    if response_data["success"]:
                        federated_id = response_data["data"]["id"]
                        response_data["data"] = {
                            "farm_id": data["id"],
                            "federated_id": federated_id,
                            "federated_farm":  federated_farm
                        }
                        response_data["sync_federation"] = Pendingactions().sync_federation_data()
                        blocks = (data["blocks"] if "blocks" in data else [])
                        response_data["remove_blocks"]  = self.remove_blocks_from_farm(federated_id, blocks)
                        record_data = self.record_data_transformations(response_data["data"])
                        response_data["message"] = record_data["message"]
                        success = record_data["success"]
                    else:
                        success = False
                else:
                    success = False
                    message = "The farm was not found in transformations."
                    response_data["message"] = message
            response_data_list.append(response_data)
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
            local_logger.error(f"Error executing create-federation-farm: {err}")
            lock.close()
        self.update_task(success, consumed)
        local_logger.info("[x] Sent")
        return True


factory.register_task('create-federation-farm', CreateFederationFarm)
