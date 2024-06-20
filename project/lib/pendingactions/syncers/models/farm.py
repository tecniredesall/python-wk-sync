from sqlalchemy import Column, Integer, String, Float, ForeignKey
from typing import TypedDict

from lib.database import Base


class ApiFarmDict(TypedDict):
    id: int
    name: str
    extension: float
    seller: int
    address: str
    country_id: str
    state_id: str
    city_id: str
    village_id: str
    status: str
    federated_id: int

class ApiFarm(Base):
    """
    Defines the farms model
    """

    __tablename__ = "farms"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    extension = Column(Float)
    seller = Column(Integer)
    address = Column(String)
    country_id = Column(String, ForeignKey("countries.id"))
    state_id = Column(String, ForeignKey("states.id"))
    city_id = Column(String, ForeignKey("cities.id"))
    village_id = Column(String, ForeignKey("villages.id"))
    status = Column(Integer) 
    federated_id = Column(String)


    def __init__(self, id: int, name: str, extension: float, seller: int, address: str, country_id: str,
                 state_id: str, city_id: str, village_id: str, status: int, federated_id:str):
        self.id = id
        self.name = name
        self.extension = extension
        self.seller = seller
        self.address = address
        self.country_id = country_id
        self.state_id = state_id
        self.city_id = city_id
        self.village_id = village_id
        self.status = status
        self.federated_id = federated_id


    def __repr__(self) -> str:
        return f"<ApiFarm {self.id}>"


    @property
    def serialize(self) -> ApiFarmDict:
        """
        Return farms in serializeable format
        """
        return {
            "id": self.id,
            "name": self.name,
            "extension": self.extension,
            "seller": self.seller,
            "address": self.address,
            "country_id": self.country_id,
            "state_id": self.state_id,
            "city_id": self.city_id,
            "village_id": self.village_id,
            "status": self.status,
            "federated_id": self.federated_id
        }
