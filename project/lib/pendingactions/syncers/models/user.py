from sqlalchemy import Column, Integer, String
from typing import TypedDict

from lib.database import Base

class ApiuserDict(TypedDict):
    id: int
    email: str
    status: int
    password: str


class Apiuser(Base):
    """
    Defines the contracts model
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String)
    status = Column(Integer)
    password = Column(String)
    canSync = Column(Integer)


    def __init__(self, id: int, email: str, status: int, password: str, canSync: int):
        self.id = id
        self.email = email
        self.status = status
        self.password = password
        self.canSync = canSync


    def __repr__(self) -> str:
        return f"<Apiuser {self.id}>"


    @property
    def serialize(self) -> ApiuserDict:
        """
        Return users in serializeable format
        """
        return {
            "id": self.id,
            "email": self.email,
            "status": self.status,
            "password": self.password,
            "canSync": self.canSync
        }
