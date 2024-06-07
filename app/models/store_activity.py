from db import Base
from sqlalchemy import Column, Integer, String, DateTime


class StoreActivity(Base):
    __tablename__ = 'store_activities'

    id = Column(Integer, primary_key=True)
    store_id = Column(String, nullable=False)
    timestamp_utc = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)
