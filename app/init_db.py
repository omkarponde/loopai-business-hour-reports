from db import engine, Base
from models import Report, StoreTimezone, StoreBusinessHour, StoreActivity

Base.metadata.create_all(bind=engine)
