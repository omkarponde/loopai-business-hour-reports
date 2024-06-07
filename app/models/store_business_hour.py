from db import Base
from sqlalchemy import Column, Integer, String, Time
from datetime import time


class StoreBusinessHour(Base):
    __tablename__ = 'store_business_hours'

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String, nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time_local = Column(Time, nullable=False, default=time(0, 0, 0))  # Default to 00:00:00
    end_time_local = Column(Time, nullable=False, default=time(23, 59, 59))  # Default to 23:59:59
