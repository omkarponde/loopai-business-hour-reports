import sys
from pathlib import Path

# Add the parent directory of the current script to the Python path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

import pandas as pd
from models import StoreActivity
from scripts.scripts_db import get_scripts_db

FILENAME = 'store status.csv'
BATCH_SIZE = 10000
csv_file_path = parent_dir / 'data' / FILENAME

chunks = pd.read_csv(csv_file_path, chunksize=BATCH_SIZE)

with get_scripts_db() as session:
    for chunk in chunks:
        chunk['timestamp_utc'] = pd.to_datetime(chunk['timestamp_utc'], format='mixed')
        store_activities = []
        for index, row in chunk.iterrows():
            store_activity = StoreActivity(
                store_id=row['store_id'],
                timestamp_utc=row['timestamp_utc'],
                status=row['status']
            )
            store_activities.append(store_activity)

        session.add_all(store_activities)
        session.commit()
