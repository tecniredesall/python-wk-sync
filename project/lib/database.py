import motor.motor_asyncio

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from app.models.settings import get_settings

config = get_settings()

host = config.DB_HOST
port = config.DB_PORT
user = config.DB_USERNAME
password = config.DB_PASSWORD
db = config.DB_DATABASE
dbtype = config.DB_CONNECTION

SQLALCHEMY_DATABASE_URI = f"{dbtype}://{user}:{password }@{host}:{port}/{db}"

engine = create_engine(SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SilosysConnection():

    def __init__(self):
        """Initialize your database connection here."""
        self.engine = create_engine(f"{dbtype}://{user}:{password }@{host}:{port}/{db}")
        self.session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=self.engine))
        self.Base = declarative_base()


    def __str__(self):
        return 'Transformaciones database connection object'


    def __del__(self):
        if hasattr(self, 'session'):
            self.session.remove()
        if hasattr(self, 'engine'):
            self.engine.engine.dispose()


def rows_to_dict_list(cursor):
    columns = [i[0] for i in cursor.description]
    return [dict(zip(columns, row)) for row in cursor]


class MongoManagerAsync:
    class __MongoManagerAsync:
        def __init__(self):
            # Initialise mongo client
            self.client = motor.motor_asyncio.AsyncIOMotorClient(config.MONGODB_URI)


    __instance = None


    def __init__(self):
        if not MongoManagerAsync.__instance:
            MongoManagerAsync.__instance = MongoManagerAsync.__MongoManagerAsync()


    def __getattr__(self, item):
        return getattr(self.__instance, item)
