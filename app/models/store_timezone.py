from db import Base
from sqlalchemy import Column, Integer, String


class StoreTimezone(Base):
    __tablename__ = 'store_timezones'

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String, nullable=False)
    timezone_str = Column(String, nullable=False, default='America/Chicago')
