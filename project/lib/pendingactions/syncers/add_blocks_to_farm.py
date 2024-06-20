import json
import zc.lockfile

from typing import List
from fastapi import status

from app.models.settings import get_settings
from lib.logging import get_logger 
from lib.pendingactions.syncer import Syncer
from lib.pendingactions.syncer import factory
from utils.api import API
from utils.constans import APP_FEDERATION

local_logger = get_logger(__name__)
config = get_settings()


class AddBlocksToFarm(Syncer):

    def get_access(self):
        pass


    def add_blocks_to_farm(self, data):
        path = f'/producers/{data["federated_produce"]}/farms/{data["federated_farm"]}'
        payload = {
            "blocks": data["blocks"],
            "source_type": "producer",
            "destination_type": "farm"
        }
        result = API(APP_FEDERATION).patch(path, json.dumps(payload))
        if result["status"] == status.HTTP_200_OK:
            return {
                "success": True,
                "data": {"status": status.HTTP_200_OK, "message": f'The blocks {data["blocks"]} were correctly related.'}
            }
        else:
            return {
                "success": False,
                "data": {"status": status.HTTP_200_OK, "message": 'Error: {result["data"]}, the blocks {data["blocks"]} could not be made.'}
            }


    def do_sync(self) -> List:
        success = True
        response_data = {}
        consumed = True
        try:
            lock = zc.lockfile.LockFile('/tmp/flow-create-farm-block.lock')
            request_payload = self._request_payload['request_payload']
            if "federated_produce" in request_payload and "federated_farm" in request_payload and "blocks" in request_payload:
                response_data = self.add_blocks_to_farm(request_payload)
                success = response_data["success"]
                self._response_payload = response_data["data"]
            else:
                success = False
                response_data = {"message": "The data id producer, id farm of federation and the list of blocks have to be sent."}
            self._response_payload = response_data
            lock.close()
        except zc.lockfile.LockError:
            consumed = False
            message = "Another farm / block creation process is running."
            self._response_payload = {"message": message}
            local_logger.info(message)
            success = False
        except Exception as err:
            local_logger.error(f"Error executing add-blocks-to-farm: {err}")
            lock.close()
        self.update_task(success, consumed)
        local_logger.info("[x] Sent")
        return True


factory.register_task('add-blocks-to-farm', AddBlocksToFarm)
