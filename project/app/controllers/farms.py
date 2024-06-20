import json
from fastapi import status

from app.models.blocks import(
    SoilTypeAppsData,
    VarietyCoffeeAppsData,
    ShadeVarietyAppsData
)
from app.models.farms import (
    FarmsAppsPayloadModel,
    FarmsAppsData,
    ListFarmsAppsData,
    ListBlocksAppsDataByFarms,
    SealsFarmAppsData,
    ListSealsFarmAppsData
)
from app.models.producers import FiltersProducersApps
from app.models.settings import get_settings
from app.queries.farms import (
    query_farms_by_producer,
    query_farms_apps_data_by_producer
)
from lib.database import MongoManagerAsync
from utils.functions import (
    camel_to_snake,
    default
)

config = get_settings()
client = MongoManagerAsync().client
db = client['federation']

async def get_farms_by_producer(producer_id, farm_name):
    pipeline = query_farms_by_producer(producer_id, farm_name)
    list_farms = await db.producer.aggregate(pipeline).to_list(length=None)
    if len(list_farms) > 0:
        list_farms = list_farms[0]["farms"]
    return {
        "status": status.HTTP_200_OK,
        "data": json.loads(json.dumps(list_farms, default=default)),
        "filters": {
            "producer": producer_id != None,
            "farm": farm_name != None
        }
    }


def _block_parsing(blocks):
    blocks_data = []
    for block in blocks:
        seals = []
        if "seals" in block and block["seals"]:
            seals = block["seals"]
        seals = _seals_parsing(seals)
        if "platforms" in block:
            for platform in block['platforms']:
                if platform["code"] == config.CODE_PLATFORM:
                    block_item = []
                    break
                block_item = ListBlocksAppsDataByFarms(
                    federated_id = block["_id"],
                    code = platform["code"] if "code" in platform else None,
                    block_id = platform["idBlock"] if "idBlock" in platform else None,
                    sealsByBlock=seals
                )
                if "blockData" in platform:
                    block_data = platform["blockData"]
                    block_item.extension = block_data["extension"] if "extension" in block_data else None
                    block_item.measurement_unit = block_data["unitExtension"] if "unitExtension" in block_data else None
                    block_item.name = block_data["name"] if "name" in block_data else None
                    block_item.address = block_data["parsedAddress"] if "parsedAddress" in block_data else None
                    block_item.latitude = block_data["latitude"] if "latitude" in block_data else None
                    block_item.longitude = block_data["longitude"] if "longitude" in block_data else None
                    block_item.height = block_data["msl"] if "msl" in block_data else None
                if "extras" in platform:
                    type_data = "array"
                    for extras in platform["extras"]:
                        key = camel_to_snake(extras["key"])
                        if hasattr(block_item, key):
                            if extras["type"] == type_data:
                                if key == "shade_variety":
                                    item = []
                                    for extra in extras["arrayValue"]:
                                        if "valueId" in extra and "value" in extra:
                                            item.append(ShadeVarietyAppsData(
                                                shade_variety_id=extra["valueId"] if "valueId" in extra else None,
                                                shade_variety_name=extra["value"] if "value" in extra else None
                                            ))
                                    block_item.shade_variety = item if item else None
                                elif key == "soil_type":
                                    item = []
                                    for extra in extras["arrayValue"]:
                                        if "valueId" in extra and "value" in extra:
                                            item.append(SoilTypeAppsData(
                                                soil_type_id=extra["valueId"] if "valueId" in extra else None,
                                                soil_type_name=extra["value"] if "value" in extra else None
                                            ))
                                    block_item.soil_type = item if item else None
                                elif key == "variety_coffee":
                                    item = []
                                    for extra in extras["arrayValue"]:
                                        if "valueId" in extra and "value" in extra:
                                            item.append(VarietyCoffeeAppsData(
                                                variety_coffee_id=extra["valueId"] if "valueId" in extra else None,
                                                variety_coffee_name=extra["value"] if "value" in extra else None
                                            ))
                                    block_item.variety_coffee = item if item else None
                            elif not extras["value"] in ('N/A', "", "n/a"):
                                    setattr(block_item, key, extras["value"])
                            if "valueId" in extras and not extras["valueId"] in ('N/A', "", "n/a"):
                                key = (key + "_id")
                                if hasattr(block_item, key):
                                    setattr(block_item, key, extras["valueId"])
                if block_item:
                    blocks_data.append(block_item)
    return blocks_data


def _seals_parsing(seals):
    seals_data = []
    if(seals):
        for seal in seals:
            if 'seal' in seal and (not "deletedDate" in seal or ("deletedDate" in seal and not seal["deletedDate"])):
                data = ListSealsFarmAppsData(
                    code=seal['origin'],
                    id=seal['seal']['id'],
                    name=seal['seal']['name'],
                    description=seal['seal']['description'],
                    icon=seal['seal']['icon']
                )
                seals_data.append(data)
    return SealsFarmAppsData(
        total=len(seals_data),
        certifications=seals_data
    )


def separate_by_code(code, item):
    i = 0
    flag = True
    data = []
    while flag:
        if item[i].code == code:
            data.append(item[i])
            del item[i]
            i -= 1
        i += 1
        if i >= len(item):
            flag = False
    return [item, data]

def _farm_parsing(platforms, blocks, seals):
    data_platforms = []
    if blocks:
        blocks = _block_parsing(blocks)
    else:
        blocks = []
    seals = _seals_parsing(seals)
    for platform in platforms:
        if platform["code"] == config.CODE_PLATFORM:
            data_platforms = []
            break
        item = ListFarmsAppsData(
            id = platform["idFarm"] if "idFarm" in platform else None,
            code = platform["code"] if "code" in platform else None,
            seller = platform["idProducer"] if "idProducer" in platform else None,
            sealsByFarm = seals,
            blocks = []
        )
        if "farmData" in platform:
            form_data = platform["farmData"]
            item.name = form_data["name"] if "name" in form_data else None
            item.extension = form_data["extension"] if "extension" in form_data else None
            item.latitude = form_data["latitude"] if "latitude" in form_data else None
            item.longitude = form_data["longitude"] if "longitude" in form_data else None
            item.address = form_data["parsedAddress"] if "parsedAddress" in form_data else None
            item.measurement_unit = form_data["unitExtension"] if "unitExtension" in form_data else None
            item.height = form_data["msl"] if "msl" in form_data else None
        if "extras" in platform:
            for extras in platform["extras"]:
                key = camel_to_snake(extras["key"])
                if hasattr(item, key) and not extras["value"] in ('N/A', "", "n/a"):
                    setattr(item, key, extras["value"])
                if "valueId" in extras and not extras["valueId"] in ('N/A', "", "n/a"):
                    key = (key + "_id")
                    if hasattr(item, key):
                        setattr(item, key, extras["valueId"])
        if len(blocks) > 0:
            result = separate_by_code(item.code, blocks)
            item.blocks = result[1]
            blocks = result[0]
        item.totalBlocksByFarm = len(item.blocks)
        data_platforms.append(item)
    return data_platforms


def _data_parsing(data):
    farm_data = []
    if len(data) > 0:
        for farm in data[0]["farms"]:
            blocks = farm["blocks"]
            seals = farm["seals"]
            platforms = farm["platforms"]
            apps = _farm_parsing(platforms, blocks, seals)
            if apps:
                item = FarmsAppsData(
                    federated_id=farm["_id"],
                    apps= apps
                )
                farm_data.append(item)
    return farm_data


async def get_farms_apps_data_by_producer(params):
    if config.GET_APPS_FARMS:
        pipeline = query_farms_apps_data_by_producer(params)
        list_farms = await db.producer.aggregate(pipeline).to_list(length=None)
        data = _data_parsing(json.loads(
            json.dumps(list_farms, default=default)))
    else:
        data = []
    filters = FiltersProducersApps(
        identifier = params.identifier != None,
        email = params.email != None,
        phone = params.phone != None
    )
    return FarmsAppsPayloadModel(
        status= status.HTTP_200_OK,
        data= data,
        filters= filters
    )
