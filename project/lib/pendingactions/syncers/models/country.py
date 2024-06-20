from sqlalchemy import Column, Integer, String

from lib.database import Base


class ApiCountry(Base):
    """
    Defines the Country model
    """

    __tablename__ = "countries"

    id = Column(Integer, primary_key=True)
    name_en = Column(String)
