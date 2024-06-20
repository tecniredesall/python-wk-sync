from utils.constans import IDENTIDAD

def query_producer_apps_data(params):
    filter_phone = {}
    filter_email = {}
    filter_identity = {}
    if params.phone:
        filter_phone = {"$and": [
            {"platforms.phones.phoneNumber": params.phone},
            {"platforms.phones.callingCode": params.calling_code}
        ]}
    if params.email:
        filter_email = {"platforms.emails": params.email}
    if params.identifier:
        if params.identifier_name in IDENTIDAD:
            params.identifier_name = IDENTIDAD[params.identifier_name]
        filter_identity = {"$and": [
            {"platforms.idNumbers.id":  params.identifier},
            {"platforms.idNumbers.name":  params.identifier_name}
        ]}
    return [
       {
        "$match": {
            '$and': [
                {
                    'deletedDate': {
                        '$exists': False
                    }
                },
                filter_phone,
                filter_email,
                filter_identity
            ]}
        },
        {
            "$project": {
                '_id': 1,
                'platforms': 1
            }
        }
    ]

def query_farms_by_producer(producer_id, farm_name):
    filter_farm_name = {}
    if farm_name:
        filter_farm_name = {
            "platforms.farmData.name": farm_name
        }
    return [
        {
            "$match": {"_id": ObjectId(producer_id)}
        },
        {
            '$lookup': {
                'from': 'farm',
                'let': {
                    'farms_ids': '$farms'
                },
                'pipeline': [
                    {
                        '$match': {
                            '$and': [
                                {
                                    '$expr': {
                                        '$in': ['$_id', '$$farms_ids']
                                    }
                                },
                                {
                                    'deletedDate': {
                                        '$exists': False
                                    }
                                },
                                filter_farm_name
                            ]
                        }
                    }
                ],
                'as': 'farms'
            }
        },
        {
            "$project": {
                '_id' : 0,
                'farms': 1
            }
        }
    ]