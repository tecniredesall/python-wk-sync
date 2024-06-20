from fastapi import status

from app.models.settings import get_settings
from lib.logging import get_logger
from lib.pendingactions.syncer import Syncer
from lib.pendingactions.syncer import factory
from typing import List
from utils.api import API
from utils.constans import (
    APP_FEDERATION,
    APP_TRANSFORMATIONS
)
from utils.pendingactions import Pendingactions

local_logger = get_logger(__name__)
config = get_settings()

class CreateFederationProducer(Syncer):

    def get_access(self):
        pass


    #Register the federation id directly in the block table in the transformation database.
    def record_data_transformations(self, data):
        success = True
        message = ""
        if data["federated_producer"]:
            if data["federated_producer"] != data["federated_id"]:
                message = f'Transformation table producer: The producer with the id {data["seller_id"]} has the federation id {data["federated_id"]} different from the one registered in the transformations with the id {data["federated_producer"]}'
                local_logger.error(message)
                success = False
            else:
                message = f'Transformation table producer: the federation id was previously registered.'
        else:
            payload = {
                "federated": data["federated_id"]
            }
            path = f'/web/federation/producers/{data["seller_id"]}'
            response = API(APP_TRANSFORMATIONS).patch(path, payload)
            if not response["data"]:
                message = "Error while trying to update the producer."
            else:
                message = response["data"]["message"]
        return {
            "success": success,
            "message": message
        }


    #verify that the record exists in transformations and get federated_id
    def get_federation_transformations(self, seller_id):
        path = f'/web/federation/producers/{seller_id}'
        farm_data = API(APP_TRANSFORMATIONS).get(path)
        federated_id = farm_data["data"]
        if "data" in federated_id and "federated" in federated_id["data"]:
            return federated_id["data"]["federated"]
        else:
            return {
                "success": False,
                "message": f'Transformations response: {federated_id["message"]}'
            }


    #Create/update a new federation registration by consuming an endpoint.
    def send_data_fedration(self, payload):
        path = "/producers"
        response = API(APP_FEDERATION).post(path, payload)
        if response["status"] == status.HTTP_200_OK:
            return {
                "success": True,
                "data": response["data"]
            }
        else:
            return {
                "success": False,
                "response": {
                    "message":  f'Federation response ({response["status"]}): {response["data"]}',
                    "data_sent": payload
                }
            }

    def do_sync(self) -> List:
        success = True
        try:
            request_payload = self._request_payload['request_payload']
            federated_producer = self.get_federation_transformations(
                request_payload["platform"]["idProducer"]
            )
            response_data = {}
            if type(federated_producer) != dict:
                response_data = self.send_data_fedration(request_payload)
                if response_data["success"]:
                    response_data["data"] = {
                        "seller_id": request_payload["platform"]["idProducer"],
                        "federated_id": response_data["data"]["id"],
                        "federated_producer": federated_producer
                    }
                    record_data = self.record_data_transformations(response_data["data"])
                    response_data["message"] = record_data["message"]
                    success = record_data["success"]
            else:
                response_data["message"] = federated_producer["message"]
                success = federated_producer["success"]
            if success:
                sync_federation = Pendingactions().sync_federation_data()
                response_data["sync_federation"] = sync_federation
            self._response_payload = response_data
        except Exception as err:
            success = False
            if 'request_payload' in locals() and request_payload:
                local_logger.error(f"Current request_payload: {request_payload}")
            local_logger.error(f"Error executing create-federation-producer: {err}")
        self.update_task(success)
        local_logger.info("[x] Sent")
        return True


factory.register_task('create-federation-producer', CreateFederationProducer)
