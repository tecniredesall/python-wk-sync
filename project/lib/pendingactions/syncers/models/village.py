from sqlalchemy import Column, Integer, String

from lib.database import Base


class ApiVillage(Base):
    """
    Defines the village model
    """

    __tablename__ = "villages"

    id = Column(Integer, primary_key=True)
    name = Column(String)
