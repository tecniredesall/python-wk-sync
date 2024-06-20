from bson import ObjectId

from app.models.settings import get_settings
from utils.constans import IDENTIDAD

config = get_settings()


def query_blocks_by_producer(producer_id, block_name, farm_id):
    filter_block_name = {}
    filter_farm_id = {}
    filter_union = ["$farms.blocks"]
    if block_name:
        filter_block_name = {'platforms.blockData.name':{
            "$regex": f".*{block_name}.*",
            "$options": "i"
            }
        }
    if farm_id:
        filter_farm_id = {
            "_id": ObjectId(farm_id)
        }
    else:
        filter_union.append("$blocks")
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
                                filter_farm_id
                            ]
                        }
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
                        '$lookup': {
                            'from': 'block',
                            'let': {
                                'blocks_ids': '$blocks'
                            },
                            'pipeline': [
                                {
                                    '$match': {
                                        '$and': [
                                            {
                                                '$expr': {
                                                    '$in': ['$_id', '$$blocks_ids']
                                                }
                                            },
                                            {
                                                'deletedDate': {
                                                    '$exists': False
                                                }
                                            },
                                            filter_block_name
                                        ]
                                    }
                                }
                            ],
                            'as': 'blocks'
                        }
                    },
                    { '$project': { 'blocks':1 } }
                ],
                'as': 'farms'
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
                            '$and': [
                                {
                                    '$expr': {
                                        '$in': ['$_id', '$$blocks_ids']
                                    }
                                },
                                {
                                    'deletedDate': {
                                        '$exists': False
                                    }
                                },
                                filter_block_name
                            ]
                        }
                    }
                ],
                'as': 'blocks'
            }
        },
        { "$unwind": "$farms" },
        {
            "$project": {
                '_id' : 0,
                "data":{ "$setUnion": filter_union }
            }
        }
    ]


def query_blocks_apps_data_by_producer(params):
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
                                },
                                {
                                    "$expr": {
                                        '$gte': [{'$size': "$blocks"}, 1]
                                    }
                                }
                            ]
                        }
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
                        '$lookup': {
                            'from': 'block',
                            'let': {
                                'blocks_ids': '$blocks'
                            },
                            'pipeline': [
                                {
                                    '$match': {
                                        '$and': [
                                            {
                                                '$expr': {
                                                    '$in': ['$_id', '$$blocks_ids']
                                                }
                                            },
                                            {
                                                'deletedDate': {
                                                    '$exists': False
                                                }
                                            }
                                        ]
                                    }
                                }
                            ],
                            'as': 'blocks'
                        }
                    },
                    {
                        '$project': {
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
            '$lookup': {
                'from': 'block',
                'let': {
                    'blocks_ids': '$blocks'
                },
                'pipeline': [
                    {
                        '$match': {
                            '$and': [
                                {
                                    '$expr': {
                                        '$in': ['$_id', '$$blocks_ids']
                                    }
                                },
                                {
                                    'deletedDate': {
                                        '$exists': False
                                    }
                                }
                            ]
                        }
                    },
                    {
                        '$project': {
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
                '_id': 0,
                "farms": 1,
                "blocks": 1
            }
        }
    ]


def query_blocks_by_farm_and_code(farm_id: str):
    return [
        {
            "$match": {
                '$and': [
                    {
                        'deletedDate': {
                            '$exists': False
                        }
                    },
                    {"_id": ObjectId(farm_id)}
                ]
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
                            '$and': [
                                {
                                    '$expr': {
                                        '$in': ['$_id', '$$blocks_ids']
                                    }
                                },
                                {"platforms.code": config.CODE_PLATFORM},
                                {
                                    'deletedDate': {
                                        '$exists': False
                                    }
                                }
                            ]
                        }
                    },
                    {
                        '$project': {
                            '_id': 1
                        }
                    }
                ],
                'as': 'blocks'
            }
        },
        {
            "$project": {
                '_id': 1,
                "blocks": 1
            }
        }
    ]
