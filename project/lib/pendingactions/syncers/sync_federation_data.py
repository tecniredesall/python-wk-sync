import copy
import datetime
import zc.lockfile

from bson.objectid import ObjectId
from dateutil.parser import parse
from fastapi import status
from pymongo import UpdateOne, MongoClient
from pytz import timezone
from typing import List

from app.models.settings import get_settings
from lib.logging import get_logger
from lib.pendingactions.syncer import Syncer, factory
from utils.api import API
from utils.constans import (
    APP_FEDERATION,
    APP_TRANSFORMATIONS
)


local_logger = get_logger(__name__)
config = get_settings()

class SyncFederationData(Syncer):

    def __init__(self):
        Syncer.__init__(self)
        self._seals = []
        self._removed_seals = []


    def get_access(self):
        pass


    def get_changes_from_federation(self, data):
        path = "/all/"
        scope = "all"
        visibility = "All"
        size = str(data["size"])
        page = str(data["current_page"])
        date = data["date"] if "date" in data and data["date"] else None
        path += f'?partitionKey={config.PARTITION_KEY}&scope={scope}&page={page}&size={size}&visibility={visibility}'
        if date:
            path += f'&from={date}'
        response = API(APP_FEDERATION).get(path)
        return response["data"]


    def seals_validation(self, data_seals, is_deleted):
        seals = None
        if is_deleted:
            seals = self._removed_seals.copy()
        else:
            seals = self._seals.copy()
        exist = False
        for certification in seals:
            #The producer ids and the certificate are the same
            if certification["seller_id"] == data_seals["seller_id"] and data_seals["certification_id"] == certification["certification_id"]:
                #The data is completely the same
                if certification["farm_id"] == data_seals["farm_id"] and certification["block_id"] == data_seals["block_id"]:
                    exist = True
                #Both have null value
                if not data_seals["farm_id"] and not data_seals["block_id"]:
                    exist = True
                #At least farm or block has id.
                elif certification["farm_id"] and certification["block_id"]:
                    #The farm is the same but the block in the new data is null.
                    if certification["farm_id"] == data_seals["farm_id"] and not data_seals["block_id"]:
                        exist = True
                    #The farm is the same but the block in the new data is null.
                    elif certification["block_id"] == data_seals["block_id"] and not data_seals["farm_id"]:
                        exist = True
                #The current data have neither farm nor block.
                elif (not certification["farm_id"] and not certification["block_id"]):
                    #The new data has block.
                    if data_seals["block_id"]:
                        certification["block_id"] = data_seals["block_id"]
                    #The new data has farm.
                    if data_seals["farm_id"]:
                        certification["farm_id"] = data_seals["farm_id"]
                    exist = True
                #The current data has a data between fam or block and the other is null.
                elif (certification["farm_id"] and not certification["block_id"]) or (not certification["farm_id"] and certification["block_id"]):
                    #The current data has farm.
                    if certification["farm_id"] and not certification["block_id"]:
                        #The new data has farm equal to the current data.
                        if data_seals["farm_id"] and certification["farm_id"] == data_seals["farm_id"]:
                            #The new data if it has a block.
                            if data_seals["block_id"]:
                                certification["block_id"] = data_seals["block_id"]
                                exist = True
                    #The current data has block.
                    if certification["block_id"] and not certification["farm_id"]:
                        #The new data has block equal to the current data.
                        if data_seals["block_id"] and certification["block_id"] == data_seals["block_id"]:
                            #The new data if it has a farms.
                            if data_seals["farm_id"]:
                                certification["farm_id"] = data_seals["farm_id"]
                                exist = True
            if exist:
                if is_deleted:
                    certification["unset"] = {
                        "seller": True if certification["unset"]["seller"] or data_seals["unset"]["seller"] else False,
                        "farm": True if certification["unset"]["farm"] or data_seals["unset"]["farm"] else False,
                        "block": True if certification["unset"]["block"] or data_seals["unset"]["block"] else False
                    }
                break
        if is_deleted:
            self._removed_seals = seals.copy()
        else:
            self._seals = seals.copy()
        return exist


    #separation of the seals that come from sylosis
    def seals_parsing(self, data, origin):
        platform  = data["platform"]
        seals = data["seals"]
        data_seals = {
            "seller_id": None,
            "certification_id": None,
            "farm_id": None,
            "block_id": None
        }
        if "idBlock" in platform and platform["idBlock"] and "idProducer" in platform and platform["idProducer"]:
            data_seals["farm_id"] = platform["idFarm"] if "idFarm" in platform and platform["idFarm"] else None
            data_seals["block_id"] = platform["idBlock"]
            data_seals["seller_id"] = platform["idProducer"]
        elif "idFarm" in platform and platform["idFarm"] and "idProducer" in platform and platform["idProducer"]:
            data_seals["farm_id"] = platform["idFarm"]
            data_seals["seller_id"] = platform["idProducer"]
        elif "identifiers" in platform and platform["identifiers"] and "idProducer" in platform["identifiers"] and platform["identifiers"]["idProducer"]:
            data_seals["seller_id"] = platform["identifiers"]["idProducer"]
        else:
            local_logger.error("The relationship is not well defined.")
            return False
        #Duplicate check
        for seal in seals:
            if 'seal' in seal:
                is_deleted = False
                if "deletedDate" in seal and seal["deletedDate"]:
                    is_deleted = True
                if "unset" in data_seals:
                    del data_seals["unset"]
                if "cache_seals" in data_seals:
                    del data_seals["cache_seals"]
                seal = seal['seal']
                data_seals["certification_id"] = seal["id"]
                if is_deleted:
                    data_seals["unset"] = {
                        "farm": False,
                        "block": False,
                        "seller": False
                    }
                    data_seals["unset"][origin] = True
                else:
                    data_seals["cache_seals"] = {
                        "name": seal["name"],
                        "description": seal["description"],
                        "icon": seal["icon"] if seal["icon"] and len(seal["icon"]) > 5 and seal["icon"][0:5] == 'https' else None
                    }
                #Validation of current data vs list
                exist = self.seals_validation(data_seals, is_deleted)
                if not exist and not is_deleted:
                    self._seals.append(copy.copy(data_seals))
                if not exist and is_deleted:
                    self._removed_seals.append(copy.copy(data_seals))
            else:
                local_logger.info("No data on seals.")


    def cast_string_to_date(self, data, origin):
        data["createdDate"] = parse(data["createdDate"])
        data["updatedDate"] = parse(data["updatedDate"])
        exist_seals = False
        exist_silosys= False
        seals_data = {}
        for platform in data["platforms"]:
            if platform["code"] == config.CODE_PLATFORM:
                exist_silosys = True
                seals_data["platform"] = platform
            platform["createdDate"] = parse(platform["createdDate"])
            platform["updatedDate"] = parse(platform["updatedDate"])
            if "extras" in platform and platform["extras"]:
                for extra in platform["extras"]:
                    if "updatedDate" in extra and extra["updatedDate"]:
                        extra["updatedDate"] = parse(extra["updatedDate"])
                    if "createdDate" in extra and extra["createdDate"]:
                        extra["createdDate"] = parse(extra["createdDate"])
        if "deletedDate" in data and data["deletedDate"]:
            data["deletedDate"] = parse(data["deletedDate"])
        if "seals" in data and data["seals"]:
            exist_seals = True
            seals_data["seals"] = data["seals"]
            for seal in data["seals"]:
                seal["createdDate"] = parse(seal["createdDate"])
                if "deletedDate" in seal and seal["deletedDate"]:
                    tz = timezone("GMT0")
                    date_cero = datetime.datetime.fromtimestamp(0, tz)
                    seal["deletedDate"] = parse(seal["deletedDate"])
                    if seal["deletedDate"] == date_cero:
                        del seal["deletedDate"]
        if exist_seals and exist_silosys:
            self.seals_parsing(seals_data, origin)
        return data


    def update_local_data(self, records):
        data_producer = []
        data_farm = []
        data_block = []
        origin = {
            "producer": "seller",
            "farm": "farm",
            "block": "block"
        }
        for record in records:
            farms = (record["farms"] if record["farms"] else [])
            blocks = (record["blocks"] if record["blocks"] else [])
            producer = self.cast_string_to_date(record, origin["producer"])
            producer["farms"] = []
            producer["blocks"] = [ObjectId(block["id"]) for block in blocks]
            for farm in farms:
                farm = self.cast_string_to_date(farm, origin["farm"])
                producer["farms"].append(ObjectId(farm["id"]))
                if "blocks" in farm and farm["blocks"]:
                    for i in range(len(farm["blocks"])):
                        blocks.append(farm["blocks"][i])
                        farm["blocks"][i] = ObjectId(farm["blocks"][i]["id"])
                data_farm.append(UpdateOne(
                    {'_id': ObjectId(farm.pop("id"))},
                    {"$set": farm},
                    upsert=True
                ))
            for block in blocks:
                block = self.cast_string_to_date(block, origin["block"])
                data_block.append(UpdateOne(
                    {'_id': ObjectId(block.pop("id"))},
                    {"$set": block},
                    upsert=True
                ))
            data_producer.append(UpdateOne(
                {'_id': ObjectId(producer.pop("id"))},
                {"$set": producer},
                upsert=True
            ))
        with MongoClient(config.MONGODB_URI) as connection:
            db = connection.federation
            if data_producer:
                result = db.producer.bulk_write(data_producer)
                local_logger.info('Updated producer %s' % repr(result.bulk_api_result))
            if data_farm:
                result = db.farm.bulk_write(data_farm)
                local_logger.info('Updated farm %s' % repr(result.bulk_api_result))
            if data_block:
                result = db.block.bulk_write(data_block)
                local_logger.info('Updated block %s' % repr(result.bulk_api_result))


    def get_and_update_data(self, params):
        if params["current_page"] > params["total_pages"]:
            return {"success": True}
        updated_data = self.get_changes_from_federation(params)
        if not "data" in updated_data:
            return {"success": False, "response": updated_data}
        if not updated_data["data"]:
            return {"success": True, "message": "There is no data to update."}
        self.update_local_data(updated_data["data"])
        params["total_pages"] = updated_data["pagination"]["pages"]
        local_logger.info(f'[x] Updated page {params["current_page"]} of {params["total_pages"]}')
        params["current_page"] += 1
        return self.get_and_update_data(params)


    def get_date_from(self, payload):
        date_from = None
        if payload:
            date_from = payload["from"]
        else:
            with MongoClient(config.MONGODB_URI) as connection:
                db = connection.worker_sync
                pending_register = db.pendingactions.find({"successful": True, "action":"sync-federation-data"}).sort('received', -1).limit(1)
                if pending_register.count() > 0:
                    minutes = datetime.timedelta(minutes=1)
                    date_from = (pending_register[0]["received"] - minutes).strftime("%Y-%m-%dT%H:%M:%S+0000")
        return date_from


    def send_seals_to_transformations(self):
        path = "/web/federated-seals"
        response = API(APP_TRANSFORMATIONS).post(path, self._seals)
        if response["status"] == status.HTTP_200_OK:
            return {
                "message": "The seals were sent to transformations successfully.",
                "success": True
            }
        else:
            if "data" in response["data"]:
                response = response["data"]["data"]
            else:
                response = response["data"]
            return {
                "response": {
                    "message": "There was an error sending to transformations",
                    "response": response
                },
                "success": False
            }


    def send_seals_to_transformations_to_remove(self):
        path = "/web/seals/remove"
        response = API(APP_TRANSFORMATIONS).put(path, self._removed_seals)
        reponse_payload = response["data"]
        if "data" in response["data"]:
            reponse_payload = response["data"]["data"]
        data = {
            "response": {
                "message": "The seals were sent to transformations successfully.",
                "response": reponse_payload
            },
            "success": True
        }
        if response["status"] != status.HTTP_200_OK:
            data["response"]["message"] = "There was an error sending to transformations"
            data["success"] = False
        return data


    def do_sync(self) -> List:
        success = True
        try:
            lock = zc.lockfile.LockFile('/tmp/sync-federation-data.lock')
            payload = self._request_payload['request_payload']
            params_federation = {
                "date": None,
                "current_page": 1,
                "size": 100,
                "total_pages": 1
            }
            date_from = self.get_date_from(payload)
            params_federation["date"] = date_from
            response = {
                "status": status.HTTP_200_OK,
                "date": date_from,
                "message": "Updated data."
            }
            federation_response = self.get_and_update_data(params_federation)
            if federation_response["success"]:
                if self._seals:
                    self._seals = sorted(self._seals, key=lambda i: (i["seller_id"], i["certification_id"]))
                    response_seals = self.send_seals_to_transformations()
                    if response_seals["success"]:
                        response["seals"] = response_seals["message"]
                    else:
                        response["seals"] = response_seals["response"]
                        success = False
                else:
                    response["seals"] = "No new seals found for silosys."
                if success and self._removed_seals:
                    self._removed_seals = sorted(self._removed_seals, key=lambda i: (i["unset"]['seller'], i["seller_id"], i["certification_id"]))
                    response_seals = self.send_seals_to_transformations_to_remove()
                    response["removed_seals"] = response_seals["response"]
                    if not response_seals["success"]:
                        success = False
                else:
                    response["removed_seals"] = "There are no new stamps to remove."
                if "message" in federation_response and federation_response["message"]:
                    response["message"] = federation_response["message"]
            else:
                response = {
                    "date": date_from,
                    "federation": federation_response["response"]
                }
                success = False
            lock.close()
        except zc.lockfile.LockError:
            message = "Another data sync process from federation is already running."
            response = {"message": message}
            local_logger.info(message)
            success = False
        except Exception as err:
            success = False
            local_logger.error(f"Error executing sync-federation-data: {err}")
            lock.close()
            local_logger.error(f'Error: {err}')
        self._response_payload = response
        self.update_task(success)
        local_logger.info("[x] Sent")
        return True


factory.register_task('sync-federation-data', SyncFederationData)
