from pydantic import BaseModel
from typing import Optional, List

from app.models.producers import (
    FiltersProducersApps
)

class ListSealsBlockAppsData(BaseModel):
    code: Optional[str]
    id: Optional[str]
    name: Optional[str]
    description: Optional[str]
    icon: Optional[str]


class SealsBlockAppsData(BaseModel):
    total: int
    certifications: List[ListSealsBlockAppsData]

class ShadeVarietyAppsData(BaseModel):
    shade_variety_id: Optional[str]
    shade_variety_name: Optional[str]


class VarietyCoffeeAppsData(BaseModel):
    variety_coffee_id: Optional[str]
    variety_coffee_name: Optional[str]


class SoilTypeAppsData(BaseModel):
    soil_type_id: Optional[str]
    soil_type_name: Optional[str]


class FarmsAppsDataByBlocks(BaseModel):
    id: str
    code: str
    name: Optional[str]
    federated_id: str
    extension: Optional[float]
    measurement_unit: Optional[str]
    wasteland_area: Optional[str]
    productive_area: Optional[str]
    measurement_type: Optional[str]
    measurement_type_id: Optional[str]
    measurement_unit_id: Optional[str]
    height: Optional[float]
    latitude: Optional[float]
    longitude: Optional[float]
    address: Optional[str]
    country_id: Optional[str]
    country: Optional[str]
    state_id: Optional[str]
    state: Optional[str]
    city_id: Optional[str]
    city: Optional[str]
    village_id: Optional[str]
    village: Optional[str]
    status: Optional[str]
    sealsByFarm: SealsBlockAppsData


class ListBlocksAppsData(BaseModel):
    block_id: str
    code: str
    seller_id: str
    farm_id: Optional[str]
    name: Optional[str]
    extension: Optional[float]
    seller: Optional[str]
    measurement_unit_height: Optional[str]
    measurement_unit: Optional[str]
    height: Optional[float]
    latitude: Optional[float]
    longitude: Optional[float]
    address: Optional[str]
    country_id: Optional[str]
    country: Optional[str]
    state_id: Optional[str]
    state: Optional[str]
    city_id: Optional[str]
    city: Optional[str]
    village_id: Optional[str]
    village: Optional[str]
    status: Optional[str]
    shade_variety: Optional[List[ShadeVarietyAppsData]]
    soil_type: Optional[List[SoilTypeAppsData]]
    variety_coffee: Optional[List[VarietyCoffeeAppsData]]
    sealsByBlock: Optional[SealsBlockAppsData]
    farm: Optional[List[FarmsAppsDataByBlocks]]


class blocksAppsData(BaseModel):
    federated_id: Optional[str]
    apps: Optional[List[ListBlocksAppsData]]


class BlocksAppsPayloadModel(BaseModel):
    status: int
    data: Optional[List[blocksAppsData]]
    filters: FiltersProducersApps
