from bson import ObjectId

from utils.constans import IDENTIDAD

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


def query_farms_apps_data_by_producer(params):
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
                ]
            }
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
                                }
                            ]
                        },
                    },
                    {
                        "$addFields": {
                            "blocks": {
                                "$cond": {
                                    "if": {
                                        "$ne": [{"$type": "$blocks"}, "array"]
                                    },
                                    "then": [],
                                    "else": "$blocks"
                                }
                            }
                        }
                    },
                    {
                        "$addFields": {
                            "seals": {
                                "$filter": {
                                    "input": "$seals",
                                    "as": "seal",
                                    "cond": {
                                        "$not": ["$$seal.deletedDate"]
                                    }
                                }
                            }
                        }
                    },
                    {
                        '$lookup': {
                            'from': 'block',
                            'let': {
                                'blocks_ids': '$blocks'
                            },
                            'pipeline': [
                                {
                                    '$match': {
                                        '$expr': {
                                            '$in': ['$_id', '$$blocks_ids']
                                        }
                                    }
                                },
                                {
                                    "$addFields": {
                                        "seals": {
                                            "$filter": {
                                                "input": "$seals",
                                                "as": "seal",
                                                "cond": {
                                                    "$not": ["$$seal.deletedDate"]
                                                }
                                            }
                                        }
                                    }
                                },
                                {
                                    "$project": {
                                        '_id': 1,
                                        'platforms': 1,
                                        'seals': 1
                                    }
                                }
                            ],
                            'as': 'blocks'
                        }
                    },
                    {
                        "$project": {
                            '_id': 1,
                            'platforms': 1,
                            'blocks': 1,
                            'seals': 1
                        }
                    }
                ],
                'as': 'farms'
            }
        },
        {
            "$project": {
                '_id': 1,
                'farms': 1
            }
        }
    ]
