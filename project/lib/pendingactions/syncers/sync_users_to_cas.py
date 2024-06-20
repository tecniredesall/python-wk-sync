import boto3
import json

from typing import List

from lib.logging import get_logger
from app.models.settings import get_settings
from lib.database import SilosysConnection
from lib.pendingactions.syncer import Syncer
from lib.pendingactions.syncer import factory
from lib.pendingactions.syncers.models.user import Apiuser

local_logger = get_logger(__name__)
config = get_settings()

class SyncUsersToCas(Syncer):

    def __init__(self):
        Syncer.__init__(self)
        self._db_transformations = SilosysConnection()
        self._sqs = None


    def __del__(self):
        del self._db_transformations


    def validate_user(self, id_user):
        can_sync = 1 
        user = self._db_transformations.session.query(Apiuser).filter(Apiuser.id == id_user, Apiuser.canSync == can_sync).first()
        return user


    def get_access(self):
        self._sqs = boto3.client(
            'sqs',
            region_name = config.AWS_REGION,
            aws_access_key_id = config.AWS_ACCESS_KEY_ID, 
            aws_secret_access_key = config.AWS_SECRET_ACCESS_KEY
        )


    def send_message(self, message, data):
        DATA_TYPE = "String"
        TYPE = 'REQUEST_WORKER'
        DESTINATION = '-'
        response = self._sqs.send_message(
            QueueUrl=(config.AWS_QUEUE_URL + config.AWS_QUEUE_NAME),
            MessageBody=message,
            MessageGroupId=data["group"],
            MessageAttributes= {
                    "ACTION": {
                        "StringValue": data["action"],
                        "DataType": DATA_TYPE
                    },
                    "DESTINATION": {
                        "StringValue": DESTINATION,
                        "DataType": DATA_TYPE
                    },
                    "TYPE": {
                        "StringValue": TYPE,
                        "DataType": DATA_TYPE
                    }
                }
        )
        return response


    def do_sync(self) -> List:
        success = True
        action = ['removeUser', 'createOrUpdateEmailUser']
        try:
            payload = self._request_payload['request_payload']
            message = json.loads(payload["message"])
            user = self.validate_user(int(message["id"]))
            if user:
                if payload["action"] in action:
                    message = {
                        "id":user.id
                    }
                    if payload["action"] == action[1]:
                        message = {
                            "id":user.id,
                            "email": user.email,
                            "status": user.status,
                            "password": user.password
                        }
                    response = self.send_message(json.dumps(message), payload)
                    self._response_payload = {
                        "message": message,
                        "response": response
                    }
                else:
                    success = False
                    message = "Action sent invalid on sync-users-to-cas, payload: {payload}."
                    local_logger.error(message)
                    self._response_payload = {
                        "message": message
                    }
            else:
                success = False
                message = "The user does not have permissions to be synchronized."
                local_logger.info(message)
                self._response_payload = {
                    "message": message
                }
        except Exception as err:
            success = False
            local_logger.error(f"Error executing sync-users-to-cas: {err}")
        local_logger.info("[x] Sent")
        self.update_task(success)
        return True


factory.register_task('sync-users-to-cas', SyncUsersToCas)
