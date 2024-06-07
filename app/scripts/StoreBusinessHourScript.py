import sys
from pathlib import Path
from datetime import datetime

# Add the parent directory of the current script to the Python path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

import pandas as pd
from models import StoreBusinessHour
from scripts.scripts_db import get_scripts_db

FILENAME = 'Menu hours.csv'

BATCH_SIZE = 10000
csv_file_path = parent_dir / 'data' / FILENAME

chunks = pd.read_csv(csv_file_path, chunksize=BATCH_SIZE)

with get_scripts_db() as session:
    for chunk in chunks:
        chunk['start_time_local'].fillna('00:00:00', inplace=True)
        chunk['end_time_local'].fillna('23:59:59', inplace=True)

        chunk['start_time_local'] = chunk['start_time_local'].apply(lambda x: datetime.strptime(x, '%H:%M:%S').time())
        chunk['end_time_local'] = chunk['end_time_local'].apply(lambda x: datetime.strptime(x, '%H:%M:%S').time())

        business_hours = []
        for index, row in chunk.iterrows():
            business_hour = StoreBusinessHour(
                store_id=row['store_id'],
                day_of_week=row['day'],
                start_time_local=row['start_time_local'],
                end_time_local=row['end_time_local']
            )
            business_hours.append(business_hour)

        session.add_all(business_hours)
        session.commit()

print("Inserted data into store_business_hours table, including defaults for stores with missing data.")
