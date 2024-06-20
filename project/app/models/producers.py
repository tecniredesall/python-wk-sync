from fastapi import HTTPException, status
from pydantic import BaseModel, root_validator, Field
from typing import Optional, List
from validate_email import validate_email
from app.models.settings import get_settings

config = get_settings()

class _ExtrasSchema(BaseModel):
    key: str
    label: str
    value: str
    type: str
    valueId: Optional[str] = Field(None, alias='id')


class ProducerIncomingPayloadSchema(BaseModel):
    id: str
    federated_id: Optional[str]
    name:str
    paternal_last: str
    identifier: str
    identifier_name: str
    address: str
    city_id: str
    city: str
    country_id: str
    country: str
    state_id: str
    state: str
    town_id: Optional[str]
    town: Optional[str]
    phone: Optional[str]
    calling_code: Optional[str]
    email: Optional[str]
    date_birth: str
    extras: Optional[List[_ExtrasSchema]]

    @root_validator
    def validate_dependencies(cls, values):
        if values.get('email'):
            values['email'] = values['email'].strip()
            if not validate_email(values['email'], check_mx=False):
                raise ValueError('Invalid email address')

        if phone := values.get('phone'):
            values['phone'] = values['phone'].strip()
            if calling_code := values.get('calling_code'):
                values['calling_code'] = values['calling_code'].strip()
            else:
                values['calling_code'] = "+000"
        else:
            values['calling_code'] = None

        if bool(values.get('town_id')) ^ bool(values.get('town')):
            raise ValueError('If town is present then town_id must be as well and vice versa')

        return values

    def get_model_schema(self):
        if self.extras:
            for i in range(len(self.extras)):
                self.extras[i] = dict(self.extras[i])
        return {
            "idFederated":  self.federated_id,
            "firstName": self.name,
            "lastName": self.paternal_last,
            "dateOfBirth": self.date_birth,
            "phoneNumber": self.phone,
            "callingCode": self.calling_code,
            "platform": {
                "idProducer": self.id,
                "code": config.CODE_PLATFORM,
            },
            "idNumber": {
                "id": self.identifier,
                "name": self.identifier_name
            },
            "address": {
                "addressLine1": self.address,
                "idCountry": self.country_id,
                "country": self.country,
                "idState": self.state_id,
                "state": self.state,
                "idVillage": self.town_id,
                "village": self.town,
                "idCity": self.city_id,
                "city": self.city
            },
            "email": self.email,
            "_partitionKey": config.PARTITION_KEY,
            "silosysInstance": config.SILOSYS_INSTANCE,
            "extras": self.extras
        }


class ProducerDataByApps(BaseModel):
    identifier: Optional[str]
    identifier_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    calling_code: Optional[str]

    @root_validator
    def validate_dependencies(cls, values):
        if values.get('identifier') == None and values.get('email') == None and values.get('phone') == None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "At least one of the three parameters must be sent (identifier, email, phone).")
        if values.get('email'):
            values['email'] = values['email'].strip()
            if not validate_email(values['email'], check_mx=False):
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, 'Invalid email address')

        if phone := values.get('phone'):
            values['phone'] = values['phone'].strip()
            if calling_code := values.get('calling_code'):
                values['calling_code'] = values['calling_code'].strip()
                if not values['calling_code'] or values['calling_code'] == "+":
                    values['calling_code'] = "+000"
                elif values['calling_code'][0] != "+":
                    values['calling_code'] = "+" + values['calling_code']
            else:
                values['calling_code'] = "+000"
        if identifier := values.get('identifier'):
            values['identifier'] = values['identifier'].strip()
        if identifier_name := values.get('identifier_name'):
            values['identifier_name'] = values['identifier_name'].strip()

        if bool(identifier) ^ bool(identifier_name):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, 'If identifier is present then identifier_name must be as well and vice versa')

        return values


class ListProducersAppsData(BaseModel):
    id: str
    code: str
    name: Optional[str]
    fullname: Optional[str]
    paternal_last: Optional[str]
    maternal_last: Optional[str]
    identifier: Optional[str]
    identifier_name: Optional[str]
    population_identifier: Optional[str]
    external_id: Optional[str]
    ihcafe_carnet: Optional[str]
    producer_type: Optional[str] = Field(None, alias='productor_type')
    producer_type_id: Optional[int] = Field(None, alias='productor_type_id')
    contact: Optional[str]
    phone_contact: Optional[str]
    calling_code: Optional[str]
    phone: Optional[str]
    phone_contact_code: Optional[str] = Field(
        None, alias='contac_calling_code')
    fax: Optional[str]
    mobile: Optional[str]
    email: Optional[str]
    address: Optional[str]
    zip_code: Optional[str]
    city_id: Optional[str]
    city: Optional[str]
    town_id: Optional[str]
    town: Optional[str]
    country_id: Optional[str]
    country: Optional[str]
    state_id: Optional[str]
    state: Optional[str]
    status: Optional[str]
    scholarship_id: Optional[int]
    scholarship: Optional[str]
    marital_status_id: Optional[int]
    marital_status: Optional[str]
    profession_id: Optional[int]
    profession: Optional[str]
    tax_identifier: Optional[str]
    population_identifier: Optional[str]
    date_birth: Optional[str]
    association_date: Optional[str]
    gender: Optional[str]


class ProducersAppsData(BaseModel):
    federated_id: Optional[str]
    apps: Optional[List[ListProducersAppsData]]


class FiltersProducersApps(BaseModel):
    identifier: bool
    email: bool
    phone: bool


class ProducerAppsPayloadModel(BaseModel):
    status: int
    data: Optional[ProducersAppsData]
    filters: FiltersProducersApps
