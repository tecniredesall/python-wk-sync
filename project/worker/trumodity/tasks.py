import datetime
import json
import time
import zc.lockfile

from .models import Apicontract, Sellers
from app.models.settings import get_settings
from bson import ObjectId
from lib.database import SilosysConnection
from lib.logging import get_logger
from lib.trumodity import TrumodityHandler
from pymongo import MongoClient
from utils.api import API
from utils.constans import (
    APP_TRUMMODITY,
    APP_TRANSFORMATIONS,
    PURCHASE_ORDER_STATUS
)
from worker.tasks.base import Task
from worker.trumodity.celery import trumodity_app

config = get_settings()
local_logger = get_logger(__name__)
members = dict()

@trumodity_app.task(bind=True, base=Task)
def get_trumodity_contracts(self):
    try:
        lock = zc.lockfile.LockFile('/tmp/sync-trumodity-contracts.lock')
        local_logger.info("Syncing the contracts")
        data = []
        temp_data = []
        global members

        path = "/contracts"
        req = API(APP_TRUMMODITY).get(path)["data"]
        if "data" in req and req["data"]:
            contracts = req["data"]
            contract_ids = []
            datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
            for contract in contracts:
                local_logger.info(f"Gettin' contract: {contract['id']}")
                seller = get_member(contract['seller'].split("#")[1])
                buyer = get_member(contract['buyer'].split("#")[1])
                if seller['ssn']:
                    commodity = None
                    path = f"/web/commodity/subcategory/{contract['commodity']}"
                    req = API(APP_TRANSFORMATIONS).get(path)["data"]
                    if "data" in req and req["data"]:
                        commodity = req["data"]["id"]
                    if commodity:
                        contract_ids.append(contract['id'])
                        item = {
                            'id': contract['id'],
                            'json': json.dumps(contract, sort_keys=False, indent=0).replace('\n', ' ').replace('\r', ''),
                            'date': datetime.datetime.strptime(contract['start_date'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                            'end_date': datetime.datetime.strptime(contract['end_date'], "%Y-%m-%dT%H:%M:%S.%fZ"),
                            'commodity_id': commodity,
                            'seller_id': seller['ssn'],
                            'buyer_name': buyer['name'],
                            'weight': contract['weight'],
                            'total_delivered': contract['fullFilledCommodityObligation'],
                            'unit_price': contract['pricing']['price_input'],
                            'pricing_type': contract['pricing']['pricing_type'],
                            'status': contract['status'],
                            'company_name': contract['company_name'] if contract['company_name'] else None
                        }
                        temp_data.append(item)
                    else:
                        local_logger.info(
                            f"There are no matching sub-commodity {contract['commodity']} for contract #{contract['id']}")
                else:
                    local_logger.info(
                        f"There are no ssn for contract #{contract['id']}")
            connection = SilosysConnection()
            for contract in temp_data:
                producer = connection.session.query(Sellers).filter(
                    Sellers.population_identifier == contract["seller_id"]).first()
                seller_id = producer.id if producer else producer
                if seller_id:
                    contract["seller_id"] = seller_id
                    data.append(contract)
                else:
                    local_logger.info(
                        f"There are no matching producers for contract #{contract['id']}")
            del connection
            update_contract_status(contract_ids)
            upsert_contracts(data)
            lock.close()
        else:
            lock.close()
            local_logger.error("Error consuming endpoint from trummodity.")
            return False
    except zc.lockfile.LockError:
        local_logger.error("Can't lock the file script: sync-trumodity-contracts")
        return False
    except Exception as err:
        lock.close()
        local_logger.error(f'An error occurred while migrating contracts from trumodity: {err}')
        return False
    else:
        lock.close()
        return True


@trumodity_app.task(bind=True, base=Task)
def change_settle_process_status(self, request: dict = None):
    try:
        settling_process_id = request["process_id"] if "process_id" in request else None
        slug_status = request["status"] if "status" in request else None
        partition_key = request["partition_key"] if "partition_key" in request else None
        partition_key_default = (config.PARTITION_KEY).replace("organization_id=", "")
        status = []
        if settling_process_id and partition_key_default == partition_key:
            res_status = API(APP_TRANSFORMATIONS).get("/web/settling-status")
            if res_status["status"] == 200:
                res_status = res_status["data"]
                for item in res_status["data"]:
                    status.append(item["slug"])
            local_logger.info('--- change_settle_process_status TASK ---')
            with MongoClient(self.config.MONGODB_URI) as connection:
                db = connection.worker_sync
                process = db.settling_processes.find_one({"_id": ObjectId(settling_process_id)})
                if process:
                    data = {}
                    send_status = True
                    request_data = {'status': slug_status}
                    if slug_status == PURCHASE_ORDER_STATUS["settled"]:
                        data = {
                            'movements': request["movements"] if "movements" in request else None,
                            'payment_types': request["payment_types"] if "payment_types" in request else None,
                            'subtotal': request["subtotal"] if "subtotal" in request else 0.0,
                            'total': request["total"] if "total" in request else 0.0,
                            'settled_at': request["settled_at"] if "settled_at" in request else None
                        }
                        request_data.update(data)
                    elif slug_status == PURCHASE_ORDER_STATUS["cancelled"]:
                        values = []
                        if "messages" in process:
                            values = [d["status"] for d in process["messages"] if "status" in d]
                        if (PURCHASE_ORDER_STATUS["settled"] in values):
                            local_logger.error("Sent to cancel a settled purchase order.")
                            send_status = False
                        else:
                            request_data.update({"removed": True})
                            db.pendingactions.remove({"$and": [{"action": "settle_contract_to_trumodity"}, {"request_payload.purchase_order_id": process['purchase_order_id']}]})
                    db.settling_processes.update_one(
                        {"_id": process['_id']},
                        {
                            '$set': request_data,
                            '$push': {'messages': {'status': slug_status, 'received': datetime.datetime.now()}}
                        }
                    )
                    if slug_status in status and send_status:
                        response = API(APP_TRANSFORMATIONS).put(f"/web/purchase-orders/{process['purchase_order_id']}/{slug_status}", dict(data))
                        local_logger.info('T API response %s' % repr(response))
                        if "data"in response and "status" in response["data"] and True == response["data"]['status']:
                            return True
                    else:
                        return True
        elif not partition_key or not settling_process_id:
            local_logger.error(f"The partition key or process id was not sent: {request}")
        else:
            local_logger.info(f"The partition key does not correspond to the current cooperative: {request}")
        return False
    except Exception as err:
        local_logger.error(f'Error when changing the status of the contract: {err}')
        return False


@trumodity_app.task(bind=True, base=Task)
def resend_message_for_settle(self):
    try:
        local_logger.info('--- resend_message_for_settle TASK ---')
        with MongoClient(self.config.MONGODB_URI) as connection:
            db = connection.worker_sync
            pipeline = [
                {'$match': { "status": None }},
                {'$lookup': {
                    'from': "pendingactions",
                    'localField': "purchase_order_id",
                    'foreignField': "request_payload.purchase_order_id",
                    'as': "pendingactions"
                }},
                {'$unwind': '$pendingactions'},
                {'$match': {"pendingactions.action": "settle_contract_to_trumodity"}},
                {'$project': {
                    "_id": 0,
                    "message.id": "$_id",
                    "message.commodity": "$pendingactions.request_payload.commodity",
                    "message.id_number": "$pendingactions.request_payload.id_number",
                    "message.partition_key": "$pendingactions.request_payload.partition_key",
                    "message.receiving_date": "$pendingactions.request_payload.receiving_date",
                    "message.contract_id": "$pendingactions.request_payload.contract_id",
                    "message.totalAmount": "$pendingactions.request_payload.totalAmount",
                    "message.loads": "$pendingactions.request_payload.loads",
                }},
            ]
            processes = list(db.settling_processes.aggregate(pipeline))
            for process in processes:
                message = process['message']
                message['id'] = str(message['id'])
                message['purchase_order_id'] = str(message['id'])
                TrumodityHandler.send_settling_message(message)
            return True
    except Exception as err:
        local_logger.error(f'Error while sending the message for settle: {err}')
        return False


def get_member(email):
    global members
    if(email in members):
        return members[email]
    else:
        path = f"/crs/Member/{email}"
        req = API(APP_TRUMMODITY).get(path)["data"]
        member = {}
        if "data" in req and req["data"]:
            member = req["data"]
        member = {
            '_id': email,
            'ssn': member['ssn'] if 'ssn' in member else None,
            'name': f"{member['firstName'] if 'firstName' in member else ''} {member['lastName'] if 'lastName' in member else ''}"
        }
        member['ssn'] = member['ssn'] if member['ssn'] != '_' else None
        members[email] = member
        return members[email]


def upsert_contracts(data):
    try:
        connection = SilosysConnection()
        contracts = []
        t0 = time.time()
        for responseContract in data:
            contract = connection.session.query(Apicontract).filter(
                Apicontract.id == responseContract['id']).first()
            if(contract):
                for key, value in responseContract.items():
                    setattr(contract, key, value)
                contracts.append(contract)
            else:
                contracts.append(Apicontract(**responseContract))
            connection.session.bulk_save_objects(
                contracts, update_changed_only=True)
            connection.session.commit()
            local_logger.info(
                "SQLAlchemy ORM bulk_save_objects(): Total time for " + str(len(contracts)) +
                " records " + str(time.time() - t0) + " secs")
        del connection
    except Exception as err:
       local_logger.error(f"Error while migrating contracts: {err}")


def update_contract_status(contract_ids):
    connection = SilosysConnection()
    try:
        status = 'Archived'
        connection.session.query(Apicontract).filter(Apicontract.id.notin_(contract_ids)).update(dict(status=status))
        connection.session.commit()
        local_logger.info("SQLAlchemy ORM update to deleted contracts")
    except Exception as err:
       local_logger.error(f"Error while delte contracts: {err}")
    del connection
