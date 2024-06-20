from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from typing import TypedDict

from lib.database import Base


class ApiBlockDict(TypedDict):
    block_id: str
    name: str
    seller_id: int
    farm_id: str
    height: float
    extension: float
    address: str
    country_id: str
    state_id: str
    city_id: str
    village_id: str
    variety_id: str
    latitude: str
    longitude: str
    is_enabled: bool
    federated_id: str


class ApiBlock(Base):
    """
        Defines the blocks model
    """

    __tablename__ = "prod_blocks"

    block_id = Column(String, primary_key=True)
    name = Column(String)
    seller_id = Column(Integer)
    farm_id = Column(String, ForeignKey("farms.id"))
    height = Column(Float)
    extension = Column(Float)
    address = Column(String)
    country_id = Column(String, ForeignKey("countries.id"))
    state_id = Column(String, ForeignKey("states.id"))
    city_id = Column(String, ForeignKey("cities.id"))
    village_id = Column(String, ForeignKey("villages.id"))
    variety_id = Column(String)
    latitude = Column(String)
    longitude = Column(String)
    is_enabled = Column(Boolean)
    federated_id = Column(String)


    def __init__(
        self, block_id: str, name: str, seller_id: int, farm_id: str, height: float, extension: float,
        address: str, country_id: str, state_id: str, city_id: str, village_id: str, variety_id: str,
        latitude: str, longitude: str, is_enabled: bool, federated_id: str
    ):
        self.block_id = block_id
        self.name = name
        self.seller_id = seller_id
        self.farm_id = farm_id
        self.height = height
        self.extension = extension
        self.address = address
        self.country_id = country_id
        self.state_id = state_id
        self.city_id = city_id
        self.village_id = village_id
        self.variety_id = variety_id
        self.latitude = latitude
        self.longitude = longitude
        self.is_enabled = is_enabled
        self.federated_id = federated_id


    def __repr__(self) -> str:
        return f"<ApiBlock {self.block_id}>"


    @property
    def serialize(self) -> ApiBlockDict:
        """
        Return farms in serializeable format
        """
        return {
            "block_id": self.block_id,
            "name": self.name,
            "seller_id": self.seller_id,
            "farm_id": self.farm_id,
            "height": self.height,
            "extension": self.extension,
            "address": self.address,
            "country_id": self.country_id,
            "state_id": self.state_id,
            "city_id": self.city_id,
            "village_id": self.village_id,
            "variety_id": self.variety_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "is_enabled": self.is_enabled,
            "federated_id": self.federated_id
        }
