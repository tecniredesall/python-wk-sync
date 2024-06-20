from sqlalchemy import Column, Integer, String

from lib.database import Base


class ApiCity(Base):
    """
    Defines the city model
    """

    __tablename__ = "cities"

    id = Column(Integer, primary_key=True)
    name = Column(String)
