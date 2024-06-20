import json, os
import time

from app.models.settings import get_settings
from datetime import datetime, timedelta
from fastapi import status
from pymongo import MongoClient
from tests.fuctions import(
    get_last_record,
    record_count
)
from worker.pendingactions.tasks import worker

config = get_settings()



def test_random_sorting():
    with MongoClient(config.MONGODB_URI) as connection:
        db = connection.worker_sync
        counter = db.pendingactions.count_documents({'action': 'random-sorting'})
        assert worker.send_task("worker.pendingactions.tasks.consume_pending_actions", args=['random-sorting', {"items":["a", "b", "c", "d", "e"]}])
        time.sleep(3)
        assert ((counter+1) == db.pendingactions.count_documents({'action': 'random-sorting'}))

def test_pending_sync_cas(test_app):
    environ = 'development'
    action = "sync-users-to-cas"
    total_records = record_count(action)
    request_data = {
        "action": action,
        "parent": "string",
        "request_payload": {
            "group" :"9",
            "type": "REQUEST",
            "action": "createOrUpdateEmailUser",
            "destination" : "$default_location",
            "message": "{\"id\":6}"
        }
    }

    response = test_app.post(
        "/pending-actions/",
        data=json.dumps(request_data)
    )
    content = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert content["status"] == 'true'
    current_records = record_count(action)
    total_records += 1
    while total_records != current_records:
        current_records =  record_count(action)
    task_id = get_last_record(action)
    assert type(task_id) == str

    response = test_app.get(f"/pending-actions/{task_id}")
    content = response.json()
    assert content["consumed"] == False
    assert response.status_code == status.HTTP_200_OK

    while content["consumed"] == False:
        response = test_app.get(f"/pending-actions/{task_id}")
        content = response.json()
    assert content["consumed"] == True
    assert content["successful"] == True

    if os.environ.get('APP_ENV') == environ:
        assert content["response_payload"]["response"]["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_sync_federation_data(test_app):
    yesterday = datetime.now() - timedelta(days=1)
    action = "sync-federation-data"
    total_records = record_count(action)
    request_data = {
        "action": action,
        "request_payload": {
           "from": yesterday.strftime("%Y-%m-%dT%H:%M:%S+0000")
        }
    }

    response = test_app.post(
        "/pending-actions/",
        data=json.dumps(request_data)
    )
    content = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert content["status"] == 'true'
    current_records = record_count(action)
    total_records += 1
    while total_records != current_records:
        current_records =  record_count(action)
    task_id = get_last_record(action)
    assert type(task_id) == str

    response = test_app.get(f"/pending-actions/{task_id}")
    content = response.json()
    assert content["consumed"] == False
    assert response.status_code == status.HTTP_200_OK

    while content["consumed"] == False:
        response = test_app.get(f"/pending-actions/{task_id}")
        content = response.json()
    assert content["consumed"] == True
    assert content["successful"] == True
    assert content["response_payload"]["status"] == status.HTTP_200_OK


def test_create_federation_producer(test_app):
    action = "create-federation-producer"
    total_records = record_count(action)
    request_data = {
        "id": "307",
        "federated_id": "61522cb3e57e8fbc0bce0b47",
        "name": "No Modificar",
        "paternal_last": "Corral Garcia",
        "phone": "2222222222",
        "calling_code": "+52",
        "address": "Dirección nueva",
        "identifier_name": "populationIdentifier",
        "identifier": "9182736451923",
        "city_id": "35fee7d5efe295a4af14719f",
        "city": "Arizona",
        "country_id": "aadae5593d17e88c15bf21c9",
        "country": "Honduras",
        "state_id": "88cd5c1bc124cbfdf7d31944",
        "state": "Atlántida",
        "town_id": "52b8d00edec85a4ea176366d",
        "town": "Agua Caliente",
        "date_birth": "2003-02-08",
        "extras": []
    }
    response = test_app.post(
        "/producers/verify",
        data=json.dumps(request_data)
    )
    content = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert content["pendingAction"] == 'true'
    if content["status"] == status.HTTP_200_OK:
        assert type(content["data"]) == dict
        assert content["data"]
    current_records = record_count(action)
    total_records += 1
    while total_records != current_records:
        current_records =  record_count(action)
    task_id = get_last_record(action)
    assert type(task_id) == str

    response = test_app.get(f"/pending-actions/{task_id}")
    content = response.json()
    assert content["consumed"] == False
    assert response.status_code == status.HTTP_200_OK

    while content["consumed"] == False:
        response = test_app.get(f"/pending-actions/{task_id}")
        content = response.json()
    assert content["consumed"] == True
    assert content["successful"] == True
    assert content["response_payload"]["status"] == status.HTTP_200_OK


def test_create_federation_farm(test_app):
    action = "create-federation-farm"
    total_records = record_count(action)
    request_data =  {
        "action": action,
        "request_payload": {
            "items":[
                {
                    "id": 102,
                    "name": "Finca1",
                    "address": "Castillo 34",
                    "extension": None,
                    "seller": 307,
                    "id_federated":"61522d9de57e8fbc0bce0b48"
                }
            ]
        }
    }
    len_items = len(request_data["request_payload"]["items"])
    response = test_app.post(
        "/pending-actions/",
        data=json.dumps(request_data)
    )
    content = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert content["status"] == 'true'
    current_records = record_count(action)
    total_records += 1
    while total_records != current_records:
        current_records =  record_count(action)
    task_id = get_last_record(action)
    assert type(task_id) == str

    response = test_app.get(f"/pending-actions/{task_id}")
    content = response.json()
    assert content["consumed"] == False
    assert response.status_code == status.HTTP_200_OK

    while content["consumed"] == False:
        response = test_app.get(f"/pending-actions/{task_id}")
        content = response.json()
    assert content["consumed"] == True
    assert content["successful"] == True
    response_payload = content["response_payload"]
    assert len(response_payload) == len_items
    for response_payload in response_payload:
        assert response_payload["status"] == status.HTTP_200_OK

def test_create_federation_block(test_app):
    action = "create-federation-block"
    total_records = record_count(action)
    request_data =  {
        "action": action,
        "request_payload": {
            "items":[
                {
                    "id": "82287604-99a2-4d72-babf-736fc3ed550a",
                    "name": "parcela1",
                    "address": None,
                    "extension_block": 34,
                    "seller": 307,
                    "farm": 102,
                    "federated_id": "61522ddee57e8fbc0bce0b4a",
                    "latitude": None,
                    "longitude": None,
                    "unit_extension": None,
                    "msl": None
                },
                {
                    "id": "44b3090e-84f2-4c23-8869-96c1106855c3",
                    "name": "parcela2",
                    "seller": 307,
                    "federated_id": "61522df2e57e8fbc0bce0b4b"
                }
            ]
        }
    }
    len_items = len(request_data["request_payload"]["items"])
    response = test_app.post(
        "/pending-actions/",
        data=json.dumps(request_data)
    )
    content = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert content["status"] == 'true'
    current_records = record_count(action)
    total_records += 1
    while total_records != current_records:
        current_records =  record_count(action)
    task_id = get_last_record(action)
    assert type(task_id) == str

    response = test_app.get(f"/pending-actions/{task_id}")
    content = response.json()
    assert content["consumed"] == False
    assert response.status_code == status.HTTP_200_OK

    while content["consumed"] == False:
        response = test_app.get(f"/pending-actions/{task_id}")
        content = response.json()
    assert content["consumed"] == True
    assert content["successful"] == True
    response_payload = content["response_payload"]
    assert len(response_payload) == len_items
    for response_payload in response_payload:
        assert response_payload["status"] == status.HTTP_200_OK


def test_delete_federation_farm(test_app):
    action = "delete-federation-farm"
    id_federation = "614cacd19f594972ab6f00d2"
    total_records = record_count(action)
    request_data =  {
        "action": action,
        "request_payload": {
            "federated_id": id_federation
        }
    }
    response = test_app.post(
        "/pending-actions/",
        data=json.dumps(request_data)
    )
    content = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert content["status"] == 'true'
    current_records = record_count(action)
    total_records += 1
    while total_records != current_records:
        current_records =  record_count(action)
    task_id = get_last_record(action)
    assert type(task_id) == str

    response = test_app.get(f"/pending-actions/{task_id}")
    content = response.json()
    assert content["consumed"] == False
    assert response.status_code == status.HTTP_200_OK

    while content["consumed"] == False:
        response = test_app.get(f"/pending-actions/{task_id}")
        content = response.json()
    assert content["consumed"] == True
    assert content["successful"] == True
    response_payload = content["response_payload"]
    assert response_payload["status"] == status.HTTP_200_OK


def test_delete_federation_block(test_app):
    action = "delete-federation-block"
    id_federation = "614c9ced9f594972ab6f00cb"
    total_records = record_count(action)
    request_data =  {
        "action": action,
        "request_payload": {
            "federated_id": id_federation
        }
    }
    response = test_app.post(
        "/pending-actions/",
        data=json.dumps(request_data)
    )
    content = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert content["status"] == 'true'
    current_records = record_count(action)
    total_records += 1
    while total_records != current_records:
        current_records =  record_count(action)
    task_id = get_last_record(action)
    assert type(task_id) == str

    response = test_app.get(f"/pending-actions/{task_id}")
    content = response.json()
    assert content["consumed"] == False
    assert response.status_code == status.HTTP_200_OK

    while content["consumed"] == False:
        response = test_app.get(f"/pending-actions/{task_id}")
        content = response.json()
    assert content["consumed"] == True
    assert content["successful"] == True
    response_payload = content["response_payload"]
    assert response_payload["status"] == status.HTTP_200_OK


def test_delete_federation_producer(test_app):
    action = "delete-federation-producer"
    id_federation = "614b60689f594972ab6ef68b"
    total_records = record_count(action)
    request_data =  {
        "action": action,
        "request_payload": {
            "federated_id": id_federation
        }
    }
    response = test_app.post(
        "/pending-actions/",
        data=json.dumps(request_data)
    )
    content = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert content["status"] == 'true'
    current_records = record_count(action)
    total_records += 1
    while total_records != current_records:
        current_records =  record_count(action)
    task_id = get_last_record(action)
    assert type(task_id) == str

    response = test_app.get(f"/pending-actions/{task_id}")
    content = response.json()
    assert content["consumed"] == False
    assert response.status_code == status.HTTP_200_OK

    while content["consumed"] == False:
        response = test_app.get(f"/pending-actions/{task_id}")
        content = response.json()
    assert content["consumed"] == True
    assert content["successful"] == True
    response_payload = content["response_payload"]
    assert response_payload["status"] == status.HTTP_200_OK


def test_remove_blocks_from_farm(test_app):
    action = "remove-blocks-from-farm"
    federated_farm= "61522d9de57e8fbc0bce0b48"
    blocks = [{
        "id": "44b3090e-84f2-4c23-8869-96c1106855c3",
        "name": "parcela2",
        "seller": 307,
        "federated_id":"61522df2e57e8fbc0bce0b4b"
    }]
    total_records = record_count(action)
    request_data = {
        "action": action,
        "request_payload": {
            "federated_farm": federated_farm,
            "blocks": blocks
        }
    }
    response = test_app.post(
        "/pending-actions/",
        data=json.dumps(request_data)
    )
    content = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert content["status"] == 'true'
    current_records = record_count(action)
    total_records += 1
    while total_records != current_records:
        current_records = record_count(action)
    task_id = get_last_record(action)
    assert type(task_id) == str

    response = test_app.get(f"/pending-actions/{task_id}")
    content = response.json()
    assert content["consumed"] == False
    assert response.status_code == status.HTTP_200_OK

    while content["consumed"] == False:
        response = test_app.get(f"/pending-actions/{task_id}")
        content = response.json()
    assert content["consumed"] == True
    assert content["successful"] == True
    response_payload = content["response_payload"]
    assert response_payload["success"] == True
    assert response_payload["add_blocks"]["status"] == True
    assert response_payload["create_blocks"]["status"] == True


def test_add_blocks_to_farm(test_app):
    action = "add-blocks-to-farm"
    federated_farm = "61522d9de57e8fbc0bce0b48"
    blocks = [
        "61522ddee57e8fbc0bce0b4a", "61522df2e57e8fbc0bce0b4b", 
        "61522e0be57e8fbc0bce0b4c", "61522e23e57e8fbc0bce0b4d"
    ]
    federated_produce = "61522cb3e57e8fbc0bce0b47"
    total_records = record_count(action)
    request_data = {
        "action": action,
        "request_payload": {
            "federated_farm": federated_farm,
            "federated_produce": federated_produce,
            "blocks": blocks
        }
    }
    response = test_app.post(
        "/pending-actions/",
        data=json.dumps(request_data)
    )
    content = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert content["status"] == 'true'
    current_records = record_count(action)
    total_records += 1
    while total_records != current_records:
        current_records = record_count(action)
    task_id = get_last_record(action)
    assert type(task_id) == str

    response = test_app.get(f"/pending-actions/{task_id}")
    content = response.json()
    assert content["consumed"] == False
    assert response.status_code == status.HTTP_200_OK

    while content["consumed"] == False:
        response = test_app.get(f"/pending-actions/{task_id}")
        content = response.json()
    assert content["consumed"] == True
    assert content["successful"] == True
    response_payload = content["response_payload"]
    assert response_payload["success"] == True
    assert response_payload["data"]["status"] == status.HTTP_200_OK


def test_create_federation_producer_farm_block(test_app):
    action = "create-federation-producer-farm-block"
    total_records = record_count(action)
    request_data = {
        "action": action,
        "request_payload": {
            "items": [{
                "producer": 542,
                "farm": 556,
                "block": "06cb5382-2522-49f8-a489-e0267a051d52"
            }]
        }
    }

    response = test_app.post(
        "/pending-actions/",
        data=json.dumps(request_data)
    )
    content = response.json()
    assert response.status_code == status.HTTP_201_CREATED
    assert content["status"] == 'true'
    current_records = record_count(action)
    total_records += 1
    while total_records != current_records:
        current_records = record_count(action)
    task_id = get_last_record(action)
    assert type(task_id) == str

    response = test_app.get(f"/pending-actions/{task_id}")
    content = response.json()
    assert content["consumed"] == False
    assert response.status_code == status.HTTP_200_OK

    while content["consumed"] == False:
        response = test_app.get(f"/pending-actions/{task_id}")
        content = response.json()
    assert content["consumed"] == True
    assert content["successful"] == True
