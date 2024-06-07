from fastapi import APIRouter, status, Depends, BackgroundTasks
from dependencies import get_db
from db import Session
from fastapi.exceptions import HTTPException
from models import Report
from schemas import ReportId
import uuid
from fastapi.responses import JSONResponse, FileResponse
from utils import generate_report
import os

app_router = APIRouter(
    prefix=''
)


@app_router.post("/trigger_report")
async def trigger_report(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    report_id = uuid.uuid4()
    new_report = Report(id=report_id, status='Running')
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    # Start the background task for report generation
    background_tasks.add_task(generate_report, new_report.id, db)

    return JSONResponse(content={'report_id': str(new_report.id)})


@app_router.get("/get_report", status_code=status.HTTP_200_OK)
async def get_report(report_id: str, db: Session = Depends(get_db)):
    # Validate uuid
    ReportId.validate_report_id(report_id)

    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found."
        )

    if report.status == 'Running':
        return {
            "Report status": "Running"
        }
    elif report.status == 'Completed':
        folder_name = 'reports'
        csv_filename = f'store_activity_report_{report_id}.csv'
        csv_filepath = os.path.join(folder_name, csv_filename)

        if os.path.exists(csv_filepath):
            return FileResponse(path=csv_filepath, filename=csv_filename, media_type='text/csv')
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="CSV file not found."
            )

    return {
        "Report status": report.status
    }
