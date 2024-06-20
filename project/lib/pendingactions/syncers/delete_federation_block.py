from typing import List
from fastapi import status

from app.models.settings import get_settings
from lib.logging import get_logger 
from lib.pendingactions.syncer import Syncer
from lib.pendingactions.syncer import factory
from utils.api import API
from utils.constans import APP_FEDERATION
from utils.pendingactions import Pendingactions

local_logger = get_logger(__name__)
config = get_settings()


class DeleteFederationBlock(Syncer):

    def get_access(self):
         pass


    def delete_block_fedration(self, block_id):
        path = f"/blocks/{block_id}"
        response = API(APP_FEDERATION).delete(path)
        message = "The block was successfully removed."
        if "data" in response:
            message = response["data"]
        return {
            "status": response["status"],
            "federated_id": block_id,
            "message": message
        }


    def do_sync(self) -> List:
        success = True
        response_data = {}
        try:
            request_payload = self._request_payload['request_payload']
            if "federated_id" in request_payload:
                federated_id = request_payload["federated_id"]
                response_data = self.delete_block_fedration(federated_id)
                if response_data["status"] == status.HTTP_200_OK:
                    sync_federation = Pendingactions().sync_federation_data()
                    response_data["sync_federation"] = sync_federation
                else:
                    success = False
            else:
                success = False
                message = "The id of the block to delete was not sent, payload: {request_payload}."
                local_logger.error(message)
                response_data = {"message": message}
            self._response_payload = response_data
        except Exception as err:
            success = False
            local_logger.error(f"Error executing delete-federation-block: {err}")
        self.update_task(success)
        local_logger.info("[x] Sent")
        return True


factory.register_task('delete-federation-block', DeleteFederationBlock)
