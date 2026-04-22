from sqlalchemy import Column, Integer, String, Float, DateTime, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Satellite(Base):
    __tablename__ = "satellites"

    id = Column(Integer, primary_key=True)
    norad_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    line1 = Column(String, nullable=False)
    line2 = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())