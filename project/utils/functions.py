import datetime

from bson import ObjectId


def default(o):
    if isinstance(o, ObjectId):
        return str(o)
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")


def camel_to_snake(s):
    return ''.join(['_'+c.lower() if c.isupper() else c for c in s]).lstrip('_')


def clean_objects(item):
    return {k: v for k, v in item.items() if v and ((True if v.lower() != 'n/a' else False) if type(v) == str else True)}
