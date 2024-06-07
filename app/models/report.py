from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from db import Base
import uuid


class Report(Base):
    __tablename__ = 'reports'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    status = Column(String, nullable=False)
