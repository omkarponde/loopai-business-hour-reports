from fastapi import HTTPException, status
from pydantic import BaseModel
import uuid


class ReportId(BaseModel):
    report_id: str

    @classmethod
    def validate_report_id(cls, report_id: str):
        try:
            uuid.UUID(report_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid report_id. Must be a valid UUID."
            )
        return report_id
