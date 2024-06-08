import os
import csv
import uuid
import logging
from collections import defaultdict
from datetime import datetime, timedelta, time
from time import time as time2

import pytz
from sqlalchemy import and_, desc
from sqlalchemy.exc import NoResultFound

from db import Session
from models import Report, StoreActivity, StoreBusinessHour, StoreTimezone
from constants import DEFAULT_TIMEZONE, STATUS_COMPLETED, FULL_DAY, REPORT_FOLDER
from fastapi import HTTPException, status


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_store_timezones(db: Session) -> dict:
    """Fetch store timezones in a single query."""
    return {tz.store_id: tz.timezone_str for tz in db.query(StoreTimezone).all()}


def get_store_activities_within_interval(store_id: uuid.UUID, start_time: datetime, end_time: datetime, db: Session):
    """Query store activities within the specified time interval."""
    return db.query(StoreActivity).filter(
        and_(
            StoreActivity.store_id == store_id,
            StoreActivity.timestamp_utc >= start_time,
            StoreActivity.timestamp_utc <= end_time
        )
    ).all()


def get_business_hours(db: Session, store_timezones: dict) -> dict:
    """Fetch business hours for each store."""
    business_hours = defaultdict(lambda: defaultdict(list))

    for business_hour in db.query(StoreBusinessHour).all():
        store_id = business_hour.store_id
        day_of_week = business_hour.day_of_week
        store_timezone = store_timezones.get(store_id)

        if store_timezone:
            business_hours[store_id]['timezone'] = store_timezone
            business_hours[store_id][day_of_week].append(
                [business_hour.start_time_local, business_hour.end_time_local]
            )

    for store_id, store_timezone in store_timezones.items():
        if store_id not in business_hours:
            # If the business hour for a store is not mentioned, it is assumed to be open 24*7
            business_hours[store_id]['timezone'] = store_timezone
            for day_of_week in range(7):
                business_hours[store_id][day_of_week] = FULL_DAY

    return business_hours


def get_business_time_range(timestamp: datetime, business_hours: dict) -> list:
    """Get the business time range for a given timestamp."""
    timestamp_time = timestamp.time()
    timestamp_day = timestamp.weekday()

    for time_range in business_hours[timestamp_day]:
        if time_range[0] <= timestamp_time <= time_range[1]:
            return time_range

    return []


def calculate_uptime_downtime(previous_activity_status: str, current_activity_status: str,
                              date_time1: datetime, date_time2: datetime) -> list:
    """Calculate uptime and downtime between two timestamps.The timestamps must be naive date time"""
    uptime, downtime = 0, 0
    interpolated_time = (date_time1 - date_time2).total_seconds() / 3600

    # If a has unequal status for current and previous activities then the uptime and
    # downtime is half of the duration between the activities else the entire duration
    # is takes as uptime for active status and downtime for inactive status
    if current_activity_status != previous_activity_status:
        uptime += (interpolated_time / 2)
        downtime += (interpolated_time / 2)
    elif current_activity_status == 'active':
        uptime += interpolated_time
    elif current_activity_status == 'inactive':
        downtime += interpolated_time

    return [uptime, downtime]


def get_start_end_timestamps(previous_timestamp: datetime, current_timestamp: datetime,
                             previous_time_range: list, current_time_range: list) -> tuple:
    """Get the start and end timestamps for activity ranges."""
    previous_start_timestamp = previous_timestamp
    if previous_time_range:
        previous_start_timestamp = datetime.combine(previous_timestamp.date(), previous_time_range[0])

    current_end_timestamp = current_timestamp
    if len(current_time_range) > 1:
        current_end_timestamp = datetime.combine(current_timestamp.date(), current_time_range[1])

    return previous_start_timestamp, current_end_timestamp


def process_activity_ranges(current_activity_timestamp: datetime, current_activity_status: str,
                            previous_activity_timestamp: datetime, previous_activity_status: str,
                            business_hours: dict, index: int) -> tuple:
    """Process activity ranges to calculate uptime and downtime."""
    uptime = 0
    downtime = 0

    # current_activity_date_time is a naive datetime of current_activity_timestamp
    current_activity_date = current_activity_timestamp.date()
    current_activity_date_time = datetime.combine(current_activity_date, current_activity_timestamp.time())

    # previous_activity_date_time is a naive datetime of previous_activity_timestamp
    previous_activity_date = previous_activity_timestamp.date()
    previous_activity_date_time = datetime.combine(previous_activity_date, previous_activity_timestamp.time())

    current_time_range = get_business_time_range(current_activity_timestamp, business_hours)
    previous_time_range = get_business_time_range(previous_activity_timestamp, business_hours)

    previous_start_timestamp, current_end_timestamp = (
        get_start_end_timestamps(previous_activity_date_time, current_activity_date_time,
                                 previous_time_range, current_time_range))

    # If the current and previous activities lies on the same date and in the same business hours of that day,
    # The duration between them is interpolated
    if current_activity_date == previous_activity_date and current_time_range == previous_time_range:

        times = calculate_uptime_downtime(previous_activity_status, current_activity_status,
                                          previous_activity_date_time, current_activity_date_time)
        uptime += times[0]
        downtime += times[1]
    # Else the duration from the start of the business hour range of previous activity to the previous activity
    # and from the current activity to the end of the business hour range of current activity are interpolated,
    # if the start_time lies on the same date and same business hour range of the first activity then only it
    # has to be interpolated.
    else:
        if index != 0:  # index 0 means the previous_activity_timestamp is start_time
            times = calculate_uptime_downtime(previous_activity_status, previous_activity_status,
                                              previous_activity_date_time, previous_start_timestamp)
            uptime += times[0]
            downtime += times[1]

        times = calculate_uptime_downtime(current_activity_status, current_activity_status,
                                          current_end_timestamp, current_activity_date_time)
        uptime += times[0]
        downtime += times[1]

    return uptime, downtime


def finalize_uptime_downtime(end_time: datetime, previous_activity_timestamp: datetime,
                             previous_activity_status: str, business_hours: dict) -> tuple:
    """Finalize uptime and downtime calculation."""
    uptime = 0
    downtime = 0

    end_time_date = end_time.date()
    end_time_time = end_time.time()

    # previous_date_time is a naive datetime of previous_activity_timestamp
    previous_date_time = datetime.combine(previous_activity_timestamp.date(), previous_activity_timestamp.time())

    end_time_range = get_business_time_range(end_time, business_hours)
    previous_time_range = get_business_time_range(previous_activity_timestamp, business_hours)

    # If the end_time and the last activity are on the same date and same time range.
    if end_time_date == previous_activity_timestamp.date() and end_time_range == previous_time_range:
        end_time_date_time = datetime.combine(end_time_date, end_time_time)
        times = calculate_uptime_downtime(
            previous_activity_status, previous_activity_status, previous_date_time, end_time_date_time
        )
        uptime += times[0]
        downtime += times[1]

    # Else the duration between the start of the business hour of the last activity and the last activity
    # is interpolated.
    else:
        times = calculate_uptime_downtime(
            previous_activity_status, previous_activity_status,
            previous_date_time, datetime.combine(previous_activity_timestamp.date(), previous_time_range[0]))
        uptime += times[0]
        downtime += times[1]

    return uptime, downtime


def interpolate_activities(activities: list, start_time: datetime, end_time: datetime, business_hours: dict) -> list:
    """Interpolate activities to calculate uptime and downtime."""
    if not activities:
        return [0, 0]

    uptime, downtime = 0, 0

    # Converting the start_time and end_time to the local time of the store
    store_timezone = pytz.timezone(business_hours['timezone'])
    start_time = start_time.astimezone(store_timezone)
    end_time = end_time.astimezone(store_timezone)

    previous_activity_timestamp = start_time
    previous_activity_status = activities[0].status

    for index, current_activity in enumerate(activities):
        current_activity_status = current_activity.status
        # Converting the timestamp_utc to the local time of the store
        current_activity_timestamp = current_activity.timestamp_utc.astimezone(store_timezone)

        # Interpolation of uptime and downtime between current and previous activities.
        up, down = process_activity_ranges(
            current_activity_timestamp, current_activity_status,
            previous_activity_timestamp, previous_activity_status, business_hours, index)

        uptime += up
        downtime += down

        previous_activity_timestamp = current_activity_timestamp
        previous_activity_status = current_activity_status

    # The duration between the final activity and the end time is interpolated.
    up, down = finalize_uptime_downtime(end_time, previous_activity_timestamp, previous_activity_status, business_hours)
    uptime += up
    downtime += down

    return [uptime, downtime]


def is_within_business_hours(store_id: uuid.UUID, timestamp: datetime, business_hours: dict) -> bool:
    """Check if a given timestamp falls within business hours."""
    if store_id not in business_hours or not business_hours[store_id]:
        # If the business hour for a store is not mentioned, it is assumed to be open 24*7
        # and the time zone is assumed to be 'America/Chicago'
        business_hours[store_id]['timezone'] = DEFAULT_TIMEZONE
        for day_of_week in range(7):
            business_hours[store_id][day_of_week] = FULL_DAY
        return True

    store_timezone = pytz.timezone(business_hours[store_id]['timezone'])
    store_timestamp = timestamp.astimezone(store_timezone)
    weekday = store_timestamp.weekday()

    if weekday in business_hours[store_id]:
        business_hours[store_id][weekday] = sorted(business_hours[store_id][weekday])
        for start_time, end_time in business_hours[store_id][weekday]:
            if start_time <= store_timestamp.time() <= end_time:
                return True
    return False


def generate_csv(report_id: uuid.UUID, start_time: datetime, end_time: datetime,
                 activities: list, business_hours: dict) -> bool:
    """Generate a CSV report for store activities."""
    if not os.path.exists(REPORT_FOLDER):
        os.makedirs(REPORT_FOLDER)

    csv_filename = f'store_activity_report_{report_id}.csv'
    csv_filepath = os.path.join(REPORT_FOLDER, csv_filename)

    # Calculate the end time for last hour and last day
    end_time_last_hour = start_time - timedelta(hours=1)
    end_time_last_day = start_time - timedelta(days=1)

    with open(csv_filepath, mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([
            'store_id', 'uptime_last_hour(minutes)', 'downtime_last_hour(minutes)',
            'uptime_last_day(hours)', 'downtime_last_day(hours)',
            'uptime_last_week(hours)', 'downtime_last_week(hours)'
        ])

        index = 0
        while index < len(activities):
            current_store_id = activities[index].store_id
            current_store_activities = []
            previous_hour_activity_hours = [0, 0]
            previous_day_activity_hours = [0, 0]
            calculated_for_hour = False
            calculated_for_day = False

            #  Store all the activities for a particular store in current_store_activities.
            while index < len(activities) and activities[index].store_id == current_store_id:
                current_activity_timestamp = activities[index].timestamp_utc

                # If all the activities for the last hour are collected, interpolate for last hour.
                if current_activity_timestamp < end_time_last_hour and not calculated_for_hour:
                    calculated_for_hour = True
                    previous_hour_activity_hours = interpolate_activities(
                        current_store_activities, start_time, end_time_last_hour, business_hours[current_store_id])

                # If all the activities for the last day are collected, interpolate for last day.
                if current_activity_timestamp < end_time_last_day and not calculated_for_day:
                    calculated_for_day = True
                    previous_day_activity_hours = interpolate_activities(
                        current_store_activities, start_time, end_time_last_day, business_hours[current_store_id])
                current_store_activities.append(activities[index])
                index += 1

            # Finally interpolate uptime and downtime for the last week.
            previous_week_activity_hours = interpolate_activities(
                current_store_activities, start_time, end_time, business_hours[current_store_id])

            uptime_last_hour, downtime_last_hour = previous_hour_activity_hours
            uptime_last_day, downtime_last_day = previous_day_activity_hours
            uptime_last_week, downtime_last_week = previous_week_activity_hours

            csv_writer.writerow([
                current_store_id, round(uptime_last_hour * 60), round(downtime_last_hour * 60),
                round(uptime_last_day), round(downtime_last_day),
                round(uptime_last_week), round(downtime_last_week)
            ])

    return True


def generate_report(report_id: uuid.UUID, db: Session):
    """Generate a report for store activities."""
    start_report_generation = time2()
    try:
        report = db.query(Report).filter(Report.id == report_id).one()
    except NoResultFound:
        raise HTTPException(
            detail="Error while generating report, please try again.",
            status_code=status.HTTP_404_NOT_FOUND
        )

    # Fetch all the stores and their timezones that are present in the store timezones table
    store_timezones = get_store_timezones(db)
    # Get the business hours and store them in a dictionary so that the business hours
    # so that the business hours of a particular store and day can be fetched in less time
    business_hours = get_business_hours(db, store_timezones)

    current_time_str = '2023-01-25 14:11:45.290'  # Using the example timestamp, current time has to be used

    current_time = datetime.strptime(current_time_str, '%Y-%m-%d %H:%M:%S.%f')
    # start_time is the time at which the generation of report started and end_time will be a week back.
    end_time = current_time - timedelta(weeks=1)
    start_time = current_time

    # Get all the activities between start_time and end_time in stored on the basis of
    # store_id and descending order od timestamp_utc
    activities = db.query(StoreActivity).filter(
        StoreActivity.timestamp_utc >= end_time,
        StoreActivity.timestamp_utc <= start_time
    ).order_by(StoreActivity.store_id, desc(StoreActivity.timestamp_utc)).all()

    # Filtering activities that are within the business hours
    activities_within_business_hours = [
        activity for activity in activities
        if is_within_business_hours(activity.store_id, activity.timestamp_utc, business_hours)
    ]

    # Start generating the csv report.
    generate_csv(report_id, start_time, end_time, activities_within_business_hours, business_hours)

    report.status = STATUS_COMPLETED
    db.commit()

    end_report_generation = time2()

    logger.info(f"Timestamp range: {start_time} -- -- -- {end_time}")
    logger.info(f"Time taken to generate report: {end_report_generation - start_report_generation} seconds")
