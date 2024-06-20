from fastapi import status
from typing import List

from app.models.settings import get_settings
from lib.logging import get_logger
from lib.pendingactions.syncer import Syncer
from lib.pendingactions.syncer import factory
from utils.api import API
from utils.constans import (
    APP_FEDERATION,
    APP_TRANSFORMATIONS,
    IDENTIDAD,
    EXTRAS_PRODUCERS,
    EXTRAS_FARMS,
    EXTRAS_BLOCKS
)
from utils.pendingactions import Pendingactions

local_logger = get_logger(__name__)
config = get_settings()

class CreateFederationProducerFarmBlock(Syncer):
    
    def get_access(self):
        return None


    def information_processing_extras(self, data, extras_name):
        extras = []
        for key, value in extras_name.items():
            if key in data and data[key]:
                value_id = None
                array_value = []
                extra = None
                kay_id = key + '_id'
                if kay_id in data:
                    value_id = data[kay_id]
                if "array" == value["type"]:
                    for item in data[key]:
                        array_name = f'{key}_name'
                        array_id = f'{key}_id'
                        if array_name in item:
                            array_value.append({
                                "value": item[array_name],
                                "valueId": item[array_id] if array_id in item else None,
                                "type": "string"
                            })
                    data[key] = ''
                extra = {
                    "key": value["key"],
                    "label": value["label"],
                    "value": data[key],
                    "type": value["type"]
                }
                if array_value:
                    extra["arrayValue"] = array_value
                if value_id:
                    extra["valueId"] = value_id
                extras.append(extra)
        return extras


    def information_processing_dimension(self, data):
        if "dimension" in data and data["dimension"]:
            for item in  data["dimension"]:
                data[item["name"]] = item["value"]
                if "abbreviation" in item and item["abbreviation"]:
                    data[f"unit_{item['name']}"] = item["abbreviation"]
        del data["dimension"]
        return data


    def information_processing_producer(self, producer_data):
        return {
            "idFederated": producer_data["federated_id"] if "federated_id" in producer_data and producer_data["federated_id"] else None,
            "firstName": producer_data["name"],
            "lastName": producer_data["paternal_last"],
            "idNumber": {
                "id": producer_data["population_identifier"],
                "name": IDENTIDAD["population_identifier"]
            },
            "dateOfBirth": producer_data["date_birth"] if "date_birth" in producer_data and producer_data["date_birth"] else None,
            "address": {
                "addressLine1": producer_data["address"] if "address" in producer_data and producer_data["address"] else None,
                "idCountry": producer_data["country_id"] if "country_id" in producer_data and producer_data["country_id"] else None,
                "country": producer_data["country"] if "country" in producer_data and producer_data["country"] else None,
                "idState": producer_data["state_id"] if "state_id" in producer_data and producer_data["state_id"] else None,
                "state": producer_data["state"] if "state" in producer_data and producer_data["state"] else None,
                "idVillage": producer_data["village_id"] if "village_id" in producer_data and producer_data["village_id"] else None,
                "village": producer_data["village"] if "village" in producer_data and producer_data["village"] else None,
                "idCity": producer_data["city_id"] if "city_id" in producer_data and producer_data["city_id"] else None,
                "city": producer_data["city"] if "city" in producer_data and producer_data["city"] else None,
                "zipCode": producer_data["zip_code"] if "zip_code" in producer_data and producer_data["zip_code"] else None
            },
            "email": producer_data["email"] if "email" in producer_data and producer_data["email"] else None,
            "phoneNumber": producer_data["phone"] if "phone" in producer_data and producer_data["phone"] else None,
            "callingCode": producer_data["calling_code"] if "calling_code" in producer_data and producer_data["calling_code"] else None,
            "platform": {
                "code": config.CODE_PLATFORM,
                "idProducer": producer_data["id"]
            },
            "silosysInstance": config.SILOSYS_INSTANCE,
            "_partitionKey": config.PARTITION_KEY,
            "extras": self.information_processing_extras(producer_data, EXTRAS_PRODUCERS),
            "farms": [],
            "blocks": []
        }
 

    def information_processing_farm(self, farm_data):
        farm_data = self.information_processing_dimension(farm_data)
        return {
            "idFederated": farm_data["federated_id"] if "federated_id" in farm_data and farm_data["federated_id"] else None,
            "name": farm_data["name"],
            "parsedAddress": farm_data["address"] if "address" in farm_data and farm_data["address"] else None,
            "extension": farm_data["extension"] if "extension" in farm_data and farm_data["extension"] else None,
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
            "extras": self.information_processing_extras(farm_data, EXTRAS_FARMS)
        }


    def information_processing_block(self, block_data):
        block_data = self.information_processing_dimension(block_data)
        return {
            "idFederated": block_data["federated_id"] if "federated_id" in block_data and block_data["federated_id"] else None,
            "name": block_data["name"],
            "parsedAddress": block_data["address"] if "address" in block_data and block_data["address"] else None,
            "extension": block_data["extension"] if "extension" in block_data and block_data["extension"] else None,
            "_partitionKey": config.PARTITION_KEY,
            "platform": {
                "code": config.CODE_PLATFORM,
                "idProducer": block_data["seller_id"],
                "idFarm": block_data["farm_id"] if "farm_id" in block_data and block_data["farm_id"] else None,
                "idBlock": block_data["block_id"]
            },
            "latitude": block_data["latitude"] if "latitude" in block_data and block_data["latitude"] else None,
            "longitude": block_data["longitude"] if "longitude" in block_data and block_data["longitude"] else None,
            "unitExtension": block_data["unit_extension"] if "unit_extension" in block_data and block_data["unit_extension"] else None,
            "msl": block_data["height"] if "height" in block_data and block_data["height"] else None,
            "extras": self.information_processing_extras(block_data, EXTRAS_BLOCKS)
        }


    def get_data_from_transformations(self, data):
        producer_id = data["producer"] if "producer" in data else None
        query_param= {
            "farm_id": data["farm"] if "farm" in data else None,
            "block_id": data["block"] if "block" in data else None
        }
        if producer_id:
            path = f'/web/producers/{producer_id}/data'
            response_data = API(APP_TRANSFORMATIONS).get(path, query_param)
            data = response_data["data"]
            if response_data["status"] == status.HTTP_200_OK:
                producer = True if data["data"]["producer"] else False
                farm = True if data["data"]["farm"] else False
                block = True if data["data"]["block"] else False
                if producer == (producer_id != None) and farm == (query_param["farm_id"] != None) and block == (query_param["block_id"] != None):
                    return {
                        "success": True,
                        "data":  data["data"],
                        "message": f'Data found, producer: {producer}, farm: {farm} and block: {block}.'
                    }
                else:
                    message = f'Not all data found, producer: {producer}, farm: {farm} and block: {block}.'
                    local_logger.error(message)
                    return {
                        "success": False,
                        "message": message
                    }
            else:
                return {
                    "success": False,
                    "message":  f'Transformations response: {data}'
                }
        else:
            message = 'The producer field is required.'
            local_logger.error(message)
            return {
                "success": False,
                "message": message
            }


    def information_processing(self, data):
        producer = None
        blocks = []
        if data["producer"]:
            producer = self.information_processing_producer(data["producer"])
        if data["block"]:
            if "farm_id" in data["block"] and data["block"]["farm_id"]:
                blocks.append(self.information_processing_block(data["block"]))
            else:
                producer["blocks"].append(self.information_processing_block(data["block"]))
        if blocks and not data["farm"]:
            message = "If a block is sent that is related to a farm, the farm must also be sent."
            local_logger.error(message)
            return {
                "success": False,
                "message": message
            }
        if data["farm"]:
            farm = self.information_processing_farm(data["farm"])
            farm["blocks"] = blocks
            producer["farms"].append(farm)
        return {
            "success": True,
            "producer_data":  producer
        }


    def send_data_federation(self, payload):
        path = "/producers"
        response_data = API(APP_FEDERATION).post(path, payload)
        data = response_data["data"]
        if response_data["status"] == status.HTTP_200_OK:
            return {
                "success": True,
                "response":  {
                    "producer":{
                        "federated_id":data['id'],
                        "id": None
                    },
                    "message": "The data was successfully updated."
                }
            }
        else:
            return {
                "success": False,
                "response":{
                    "message":  f'Federation response ({response_data["status"]}): {data}',
                    "data_sent": payload
                }
            }


    def do_sync(self) -> List:
        success = True
        response_data_list = []
        items = self._request_payload['request_payload']['items']
        for item in items:
            response = {}
            response_transformations = self.get_data_from_transformations(item)
            if response_transformations["success"]:
                response["transformations"] = response_transformations["message"]
                data = self.information_processing(response_transformations["data"])
                if data["success"]:
                    response_federation = self.send_data_federation(data["producer_data"])
                    if response_federation["success"]:
                        response["federation"] = response_federation["response"]
                        response["federation"]["producer"]["id"] = item["producer"]
                        response["sync_federation"] = Pendingactions().sync_federation_data()
                    else:
                        success = False    
                        response["federation"] = response_federation["response"]
                else:
                    success = False
                    response["data_parsing"] = data["message"]
            else:
                success = False
                response["transformations"] = response_transformations["message"]
            response_data_list.append(response)
        self._response_payload = response_data_list
        self.update_task(success)
        return True


factory.register_task('create-federation-producer-farm-block', CreateFederationProducerFarmBlock)
