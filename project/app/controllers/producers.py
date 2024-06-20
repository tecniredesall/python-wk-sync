import json

from bson import ObjectId
from fastapi import status

from app.models.producers import (
    ProducerAppsPayloadModel,
    FiltersProducersApps,
    ProducersAppsData,
    ListProducersAppsData
)
from app.models.settings import get_settings
from app.queries.producer import (
    query_producer_apps_data
)
from lib.database import MongoManagerAsync
from lib.logging import get_logger
from utils.functions import (
    camel_to_snake,
    default
)
from utils.constans import (
    IDENTIDAD,
    ID_INTEGERS_EXTRAS,
    GENDER
)
from worker.pendingactions.tasks import worker

config = get_settings()
client = MongoManagerAsync().client
db = client['federation']

local_logger = get_logger(__name__)

#email verification on other producers
async def _verify_email_users(email):
    return await db.producer.count_documents({"platforms.emails": email})


#phone verification on other producers
async def _verify_phone_users(phone_number, calling_code):
    return await db.producer.count_documents({
        "platforms.phones.phoneNumber": phone_number,
        "platforms.phones.callingCode": calling_code
    })


async def _pending_action_creation(producer_data):
    action = "create-federation-producer"
    data = producer_data.get_model_schema()
    actionCounter = await db.actions.count_documents({
        "action" : action,
        "active" : False
    })
    if actionCounter == 0:
        worker.send_task("worker.pendingactions.tasks.consume_pending_actions", args=[action, data])
        return {'pendingAction':'true', 'message': 'Pending action created.', "data":{}}
    return {"status": status.HTTP_400_BAD_REQUEST, 'pendingAction':'false', "message": "The pending action could not be created.","data":{}}


async def validate_producer_data(producer_data):
    response = {}
    has_apps = False
    email_exists_another = 0
    phone_exists_another = 0
    if producer_data.identifier_name in IDENTIDAD:
        producer_data.identifier_name = IDENTIDAD[producer_data.identifier_name]
    search_parameters = [
        {"platforms.idNumbers.id":  producer_data.identifier},
        {"platforms.idNumbers.name":  producer_data.identifier_name}
    ]
    producer = await db.producer.find_one({"$and" : search_parameters})
    if producer_data.phone and not producer_data.calling_code:
        producer_data.calling_code = "+000"
    if producer:
        has_apps = True
        #User exists
        producer_data.federated_id = str(producer.get("_id"))
        email_exists_producer = 1
        phone_exists_producer = 1
        if producer_data.email:
            #If the email is sent, it is validated that the same producer has it
            email_exists_producer = await db.producer.count_documents({
                "_id": ObjectId(producer_data.federated_id),
                "platforms.emails": producer_data.email})
        if producer_data.phone:
            #If the phone is sent, it is validated that the same producer has it
            phone_exists_producer = await db.producer.count_documents({
                "_id": ObjectId(producer_data.federated_id),
                "platforms.phones.phoneNumber": producer_data.phone,
                "platforms.phones.callingCode": producer_data.calling_code
            })
        if email_exists_producer <= 0 or phone_exists_producer <= 0:
            #The mail or the phone, even both, do not exist in the producer's document
            if email_exists_producer <= 0:
                #The email is not owned by the producer, it is validated if another has it
                email_exists_another = await _verify_email_users(producer_data.email)
            if phone_exists_producer <= 0:
                #The phone is not owned by the producer, it is validated if another has it
                phone_exists_another = await _verify_phone_users(producer_data.phone, producer_data.calling_code)
    else:
        #Non-user exists
        if producer_data.email:
            #The email is valid if it has other products
            email_exists_another = await _verify_email_users(producer_data.email)
        if producer_data.phone:
            #The phone is valid if it has other products
            phone_exists_another = await _verify_phone_users(producer_data.phone, producer_data.calling_code)
    if email_exists_another > 0 or phone_exists_another > 0:
        error_response = {
            "status": status.HTTP_409_CONFLICT,
            "error": {"field": "email_phone", "type": "in_use", "has_apps": has_apps}
        }
        if email_exists_another > 0 and phone_exists_another > 0:
            return error_response
        elif email_exists_another > 0:
            error_response["error"]["field"] = "email"
            return error_response
        elif phone_exists_another > 0:
            error_response["error"]["field"] = "phone"
            return error_response
    #A pending action was created if the email and phone is not in use by other producers
    response = await _pending_action_creation(producer_data)
    if not "status" in response:
        response["status"] = status.HTTP_201_CREATED
        if producer:
            response["data"] = json.loads(json.dumps(producer, default=default).replace('_id', 'id'))
    return response


def _data_parsing(data):
    platforms = []
    if len(data) > 0:
        for platform in data[0]["platforms"]:
            if platform["code"] == config.CODE_PLATFORM:
                platforms = []
                break
            item = ListProducersAppsData(
                id=platform["identifiers"]["idProducer"],
                code=platform["code"]
            )
            if "emails" in platform and len(platform["emails"]) > 0:
                i = len(platform["emails"]) - 1
                item.email = platform["emails"][i]
            if "phones" in platform and len(platform["phones"]) > 0:
                i = len(platform["phones"]) - 1
                item.calling_code = platform["phones"][i]["callingCode"]
                item.phone = platform["phones"][i]["phoneNumber"]
            if "idNumbers" in platform:
                for id_number in platform["idNumbers"]:
                    if "RTN" == id_number["name"]:
                        item.tax_identifier = id_number["id"]
                    elif id_number["name"] in IDENTIDAD or id_number["name"] == "IDENTIDAD":
                        item.population_identifier = id_number["id"]
                    elif not item.identifier:
                        item.identifier = id_number["id"]
                        item.identifier_name = id_number["name"]
            if "producerData" in platform:
                prod_data = platform["producerData"]
                item.name = prod_data["firstName"] if "firstName" in prod_data else None
                item.paternal_last = prod_data["lastName"] if "lastName" in prod_data else None
                item.date_birth = prod_data["dateOfBirth"] if "dateOfBirth" in prod_data else None
                if item.name and item.paternal_last:
                    item.fullname = item.name + " " + item.paternal_last
                elif item.name:
                    item.fullname = item["name"]
                elif item.paternal_last:
                    item.fullname = item.paternal_last
                if "address" in prod_data:
                    address = prod_data["address"]
                    item.address = address["addressLine1"] if "addressLine1" in address else None
                    item.city_id = address["idCity"] if "idCity" in address else None
                    item.town_id = address["idVillage"] if "idVillage" in address else None
                    item.state_id = address["idState"] if "idState" in address else None
                    item.country_id = address["idCountry"] if "idCountry" in address else None
                    item.city = address["city"] if "city" in address else None
                    item.town = address["village"] if "village" in address else None
                    item.state = address["state"] if "state" in address else None
                    item.country = address["country"] if "country" in address else None
            if "extras" in platform:
                gender = "gender"
                for extras in platform["extras"]:
                    key = camel_to_snake(extras["key"])
                    if hasattr(item, key) and not extras["value"] in ('N/A', "", "n/a"):
                        if key == gender:
                            value = extras["value"]
                            if value.lower() in GENDER:
                                setattr(item, key, GENDER[value])
                            else:
                                setattr(item, key, GENDER["otro"])
                        else:
                            setattr(item, key, extras["value"])
                    if "valueId" in extras and not extras["valueId"] in ('N/A', "", "n/a"):
                        key = (key + "_id")
                        if hasattr(item, key):
                            value_id = extras["valueId"]
                            try:
                                if key in ID_INTEGERS_EXTRAS:
                                    value_id = int(value_id)
                                setattr(item, key, value_id)
                            except:
                                local_logger.info(
                                    f'The key {key} with value {value_id} could not be caster to integer.')
            platforms.append(item)
        if platforms:
            return ProducersAppsData(
                federated_id= data[0]["_id"],
                apps= platforms
            )
    return ProducersAppsData()


async def get_producer_apps_data(params):
    if config.GET_APPS_PRODUCERS:
        pipeline = query_producer_apps_data(params)
        list_producers = await db.producer.aggregate(pipeline).to_list(length=None)
        data = _data_parsing(json.loads(
            json.dumps(list_producers, default=default)))
        if not data.apps:
            data = {}
    else:
        data = {}
    filters = FiltersProducersApps(
        identifier=params.identifier != None,
        email=params.email != None,
        phone=params.phone != None
    )
    return ProducerAppsPayloadModel(
        status=status.HTTP_200_OK,
        data = data,
        filters=filters
    )
