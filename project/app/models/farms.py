from pydantic import BaseModel
from typing import Optional, List
from app.models.producers import (
    FiltersProducersApps
)
from app.models.blocks import(
    ShadeVarietyAppsData,
    VarietyCoffeeAppsData,
    SoilTypeAppsData
)

class ListSealsFarmAppsData(BaseModel):
    code: Optional[str]
    id: Optional[str]
    name: Optional[str]
    description: Optional[str]
    icon: Optional[str]


class SealsFarmAppsData(BaseModel):
    total: int
    certifications: List[ListSealsFarmAppsData]


class ListBlocksAppsDataByFarms(BaseModel):
    block_id: str
    code: str
    federated_id: str
    name: Optional[str]
    extension: Optional[float]
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
    sealsByBlock: SealsFarmAppsData


class ListFarmsAppsData(BaseModel):
    id: str
    code: str
    name: Optional[str]
    extension: Optional[float]
    seller: str
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
    sealsByFarm: SealsFarmAppsData
    totalBlocksByFarm: Optional[int]
    blocks: Optional[List[ListBlocksAppsDataByFarms]]
   

class FarmsAppsData(BaseModel):
    federated_id: Optional[str]
    apps: Optional[List[ListFarmsAppsData]]


class FarmsAppsPayloadModel(BaseModel):
    status: int
    data: Optional[List[FarmsAppsData]]
    filters: FiltersProducersApps
