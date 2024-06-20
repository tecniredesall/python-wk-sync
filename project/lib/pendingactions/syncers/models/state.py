from sqlalchemy import Column, Integer, String

from lib.database import Base


class ApiState(Base):
    """
    Defines the state model
    """

    __tablename__ = "states"

    id = Column(Integer, primary_key=True)
    name = Column(String)
