import json
from fastapi import status

from app.models.producers import (
    FiltersProducersApps
)
from app.models.settings import get_settings
from app.queries.blocks import (
    query_blocks_by_producer,
    query_blocks_apps_data_by_producer
)
from lib.database import MongoManagerAsync
from utils.functions import default
from app.models.blocks import (
    BlocksAppsPayloadModel,
    ListBlocksAppsData,
    ListSealsBlockAppsData,
    SealsBlockAppsData,
    ShadeVarietyAppsData,
    VarietyCoffeeAppsData,
    SoilTypeAppsData,
    FarmsAppsDataByBlocks,
    blocksAppsData
)
from utils.functions import (
    camel_to_snake,
    default
)

config = get_settings()
client = MongoManagerAsync().client
db = client['federation']


async def get_blocks_by_producer(producer_id, block_name, farm_id):
    if block_name:
        block_name = block_name.strip()
    if farm_id:
        farm_id = farm_id.strip()
    pipeline = query_blocks_by_producer(producer_id, block_name, farm_id)
    list_blocks = await db.producer.aggregate(pipeline).to_list(length=None)
    if len(list_blocks) > 0:
        list_blocks = list_blocks[0]["data"]
    return {
        "status": status.HTTP_200_OK,
        "data": json.loads(json.dumps(list_blocks, default=default)),
        "filters": {
            "producer": producer_id != None,
            "farm": farm_id != None,
            "block": block_name != None
        }
    }


def _seals_parsing(seals):
    seals_data = []
    if(seals):
        for seal in seals:
            if 'seal' in seal and (not "deletedDate" in seal or ("deletedDate" in seal and not seal["deletedDate"])):
                data = ListSealsBlockAppsData(
                    code=seal['origin'],
                    id=seal['seal']['id'],
                    name=seal['seal']['name'],
                    description=seal['seal']['description'],
                    icon=seal['seal']['icon']
                )
                seals_data.append(data)
    return SealsBlockAppsData(
        total=len(seals_data),
        certifications=seals_data
    )


def _block_parsing(block, farm: list = None):
    seals = []
    list_blocks = []
    if "seals" in block and block["seals"]:
        seals = block["seals"]
    seals = _seals_parsing(seals)
    if "platforms" in block:
        for platform in block['platforms']:
            if platform["code"] == config.CODE_PLATFORM:
                list_blocks = []
                break
            block_item = ListBlocksAppsData(
                seller_id=platform["idProducer"] if "idProducer" in platform else None,
                code = platform["code"] if "code" in platform else None,
                block_id = platform["idBlock"] if "idBlock" in platform else None,
                sealsByBlock=seals
            )
            if farm:
                block_item.farm = farm
            if "blockData" in platform:
                block_data = platform["blockData"]
                block_item.extension = block_data["extension"] if "extension" in block_data else None
                block_item.measurement_unit = block_data[
                    "unitExtension"] if "unitExtension" in block_data else None
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
            list_blocks.append(block_item)
        if list_blocks:
            return blocksAppsData(
                federated_id=block["_id"],
                apps=list_blocks
            )
    return blocksAppsData()


def _farm_parsing(farm):
    list_farm = []
    list_blocks= []
    seals = []
    if "seals" in farm and farm["seals"]:
        seals = farm["seals"]
    seals = _seals_parsing(seals)
    if "platforms" in farm:
        for platform in farm["platforms"]:
            item = FarmsAppsDataByBlocks(
                id=platform["idFarm"] if "idFarm" in platform else None,
                code=platform["code"] if "code" in platform else None,
                federated_id=farm["_id"],
                sealsByFarm=seals
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
            if platform["code"] == config.CODE_PLATFORM:
                list_farm = [item]
                break
            list_farm.append(item)
    for block in farm["blocks"]:
        block_data = _block_parsing(block, list_farm)
        if block_data.apps:
            list_blocks.append(block_data)
    return list_blocks

def _data_parsing(data):
    block_data = []
    if len(data) > 0:
        for item in data[0]["blocks"]:
            block = _block_parsing(item)
            if block.apps:
                block_data.append(block)
        for item in data[0]["farms"]:
            list_block = _farm_parsing(item)
            block_data += list_block
    return block_data


async def get_blocks_apps_data_by_producer(params):
    if config.GET_APPS_BLOCKS:
        pipeline = query_blocks_apps_data_by_producer(params)
        list_blocks = await db.producer.aggregate(pipeline).to_list(length=None)
        data = _data_parsing(json.loads(
            json.dumps(list_blocks, default=default)))
    else:
        data = []
    filters = FiltersProducersApps(
        identifier = params.identifier != None,
        email = params.email != None,
        phone = params.phone != None
    )
    return BlocksAppsPayloadModel(
        status = status.HTTP_200_OK,
        data = data,
        filters = filters
    )
