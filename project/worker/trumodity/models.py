from datetime import datetime

from lib.database import SilosysConnection
from sqlalchemy import Column, Integer, Float, String, DateTime
from typing import TypedDict

connection = SilosysConnection()
Base = connection.Base

class ApicontractDict(TypedDict):
    id: str
    json: str
    date: datetime
    end_date: datetime
    commodity_id: int
    seller_id: int
    buyer_name: str
    weight: float
    status: str
    pricing_type: str
    total_delivered: float
    unit_price: float
    company_name: str

class Apicontract(Base):
    """
    Defines the contracts model
    """

    __tablename__ = "apicontracts"

    id = Column(String, primary_key=True)
    json = Column(String)
    date = Column(DateTime)
    end_date = Column(DateTime)
    commodity_id = Column(Integer)
    seller_id = Column(Integer)
    buyer_name = Column(String)
    weight = Column(Float)
    status = Column(String)
    pricing_type = Column(String)
    total_delivered = Column(Float)
    unit_price = Column(Float)
    company_name = Column(String)

    def __init__(self, id: str, json: str, date: datetime, end_date: datetime, commodity_id: int,
                seller_id: int, buyer_name: str, weight: float, status: str, pricing_type: str,
                total_delivered: float, unit_price: float, company_name: str):
        self.id = id
        self.json = json
        self.date = date
        self.end_date = end_date
        self.commodity_id = commodity_id
        self.seller_id = seller_id
        self.buyer_name = buyer_name
        self.weight = weight
        self.status = status
        self.pricing_type = pricing_type
        self.total_delivered = total_delivered
        self.unit_price = unit_price
        self.company_name = company_name

    def __repr__(self) -> str:
        return f"<Apicontract {self.id}>"

    @property
    def serialize(self) -> ApicontractDict:
        """
        Return contract in serializeable format
        """
        return {
            "id": self.id,
            "json": self.json,
            "date": self.date,
            "end_date": self.end_date,
            "commodity_id": self.commodity_id, 
            "seller_id": self.seller_id, 
            "buyer_name": self.buyer_name,
            "weight": self.weight,
            "status": self.status, 
            "pricing_type": self.pricing_type, 
            "total_delivered": self.total_delivered,
            "unit_price": self.unit_price,
            "company_name": self.company_name,
        }

class PurchaseOrderDict(TypedDict):
    id: str
    creation_date: datetime
    edition_date: datetime
    creation_user: int
    edition_user: int
    creation_email: str
    producer_id: str
    producer_name: str
    producer_address: str
    contract_id: str
    note: str
    status: int
    settling: int
    created_at: datetime
    updated_at: datetime


class PurchaseOrder(Base):
    """
    Defines the purchase order model
    """

    __tablename__ = "prod_purchase_orders"

    id = Column(String, primary_key=True)
    creation_date = Column(DateTime)
    edition_date = Column(DateTime)
    creation_user = Column(Integer)
    edition_user = Column(Integer)
    creation_email = Column(String)
    producer_id = Column(String)
    producer_name = Column(String)
    producer_address = Column(String)
    contract_id = Column(String)
    note = Column(String)
    status = Column(Integer)
    settling = Column(Integer)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __init__(self, id: str, creation_date: datetime, edition_date: datetime, creation_user: int, edition_user: int, 
                 creation_email: str, producer_id: str, producer_name: str, producer_address: str, contract_id: str, note: str, 
                 status: int, settling: int, created_at: datetime, updated_at: datetime):
        self.id = id
        self.creation_date = creation_date
        self.edition_date = edition_date
        self.creation_user = creation_user
        self.edition_user = edition_user
        self.creation_email = creation_email
        self.producer_id = producer_id
        self.producer_name = producer_name
        self.producer_address = producer_address
        self.contract_id = contract_id
        self.note = note
        self.status = status
        self.settling = settling
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self) -> str:
        return f"<PurchaseOrder {self.id}>"

    @property
    def serialize(self) -> PurchaseOrderDict:
        """
        Return purchase order in serializeable format
        """
        return {
            "id": self.id,
            "creation_date": self.creation_date,
            "edition_date": self.edition_date,
            "creation_user": self.creation_user,
            "edition_user": self.edition_user, 
            "creation_email": self.creation_email, 
            "producer_id": self.producer_id,
            "producer_name": self.producer_name,
            "producer_address": self.producer_address, 
            "contract_id": self.contract_id, 
            "note": self.note,
            "status": self.status,
            "settling": self.settling,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class SellersDict(TypedDict):
    id: int
    name: str
    paternal_last: str
    maternal_last: str
    external_id: str
    ihcafe_carnet: str
    productor_type: int
    contact: str
    phone_contact: str
    phone: str
    fax: str
    mobile: str
    email: str
    address: str
    city_id: str
    zip_code: str
    town_id: str
    status: int
    password: str
    seller_id_parent: int
    grainchain_origin_weight: int
    source_id: int
    branch_id: int
    scholarship_id: int
    marital_status_id: int
    profession_id: int
    tax_identifier: str
    population_identifier: str
    date_birth: datetime
    association_date: datetime
    gender: str
    federated_id: str


class Sellers(Base):
    """
    Defines the seller model
    """

    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    paternal_last = Column(String)
    maternal_last = Column(String)
    external_id = Column(String)
    ihcafe_carnet = Column(String)
    productor_type = Column(Integer)
    contact = Column(String)
    phone_contact = Column(String)
    phone = Column(String)
    fax = Column(String)
    mobile = Column(String)
    email = Column(String)
    address = Column(String)
    city_id = Column(String)
    zip_code = Column(String)
    town_id = Column(String)
    status = Column(Integer)
    password = Column(String)
    seller_id_parent = Column(Integer)
    grainchain_origin_weight = Column(Integer)
    source_id = Column(Integer)
    branch_id = Column(Integer)
    scholarship_id = Column(Integer)
    marital_status_id = Column(Integer)
    profession_id = Column(Integer)
    tax_identifier = Column(String)
    population_identifier = Column(String)
    date_birth = Column(DateTime)
    association_date = Column(DateTime)
    gender = Column(String)
    federated_id = Column(String)

    def __init__(self, id: int, name: str, paternal_last: str, maternal_last : str, external_id : str, ihcafe_carnet : str, productor_type : int,
        contact : str, phone_contact : str, phone : str, fax : str, mobile : str, email : str, address : str, city_id : str, zip_code : str,
        town_id : str, status : int, password : str, seller_id_parent : int, grainchain_origin_weight : int, source_id : int, branch_id : int,
        scholarship_id : int, marital_status_id : int, profession_id : int, tax_identifier : str, population_identifier : str, date_birth: datetime,
        association_date: datetime, gender: str, federated_id: str):
        self.id = id
        self.name = name
        self.paternal_last = paternal_last
        self.maternal_last = maternal_last
        self.external_id = external_id
        self.ihcafe_carnet = ihcafe_carnet
        self.productor_type = productor_type
        self.contact = contact
        self.phone_contact = phone_contact
        self.phone = phone
        self.fax = fax
        self.mobile = mobile
        self.email = email
        self.address = address
        self.city_id = city_id
        self.zip_code = zip_code
        self.town_id = town_id
        self.status = status
        self.password = password
        self.seller_id_parent = seller_id_parent
        self.grainchain_origin_weight = grainchain_origin_weight
        self.source_id = source_id
        self.branch_id = branch_id
        self.scholarship_id = scholarship_id
        self.marital_status_id = marital_status_id
        self.profession_id = profession_id
        self.tax_identifier = tax_identifier
        self.population_identifier = population_identifier
        self.date_birth = date_birth
        self.association_date = association_date
        self.gender = gender
        self.federated_id = federated_id


    def __repr__(self) -> str:
        return f"<Sellers {self.id}>"

    @property
    def serialize(self) -> SellersDict:
        """
        Return contract in serializeable format
        """
        return {
            "id": self.id,
            "name": self.name,
            "paternal_last": self.paternal_last,
            "maternal_last": self.maternal_last,
            "external_id": self.external_id,
            "ihcafe_carnet": self.ihcafe_carnet,
            "productor_type": self.productor_type,
            "contact": self.contact,
            "phone_contact": self.phone_contact,
            "phone": self.phone,
            "fax": self.fax,
            "mobile": self.mobile,
            "email": self.email,
            "address": self.address,
            "city_id": self.city_id,
            "zip_code": self.zip_code,
            "town_id": self.town_id,
            "status": self.status,
            "password": self.password,
            "seller_id_parent": self.seller_id_parent,
            "grainchain_origin_weight": self.grainchain_origin_weight,
            "source_id": self.source_id,
            "branch_id": self.branch_id,
            "scholarship_id": self.scholarship_id,
            "marital_status_id": self.marital_status_id,
            "profession_id": self.profession_id,
            "tax_identifier": self.tax_identifier,
            "population_identifier": self.population_identifier,
            "date_birth": self.date_birth,
            "association_date": self.association_date,
            "gender": self.gender,
            "federated_id": self.federated_id
        }

del connection
