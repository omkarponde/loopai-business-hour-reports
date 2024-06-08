from datetime import time

DEFAULT_TIMEZONE = 'America/Chicago'
FULL_DAY = [(time(0, 0), time(23, 59, 59))]
REPORT_FOLDER = 'reports'

STATUS_RUNNING = "Running"
STATUS_COMPLETED = "Completed"

STORE_ACTIVITY_CSV = 'store status.csv'
STORE_BUSINESS_HOUR_CSV = 'Menu hours.csv'
STORE_TIMEZONE_CSV = 'bq-results-20230125-202210-1674678181880.csv'
