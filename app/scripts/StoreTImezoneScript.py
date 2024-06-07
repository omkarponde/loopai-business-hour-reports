import sys
from pathlib import Path
import pandas as pd

# Add the parent directory of the current script to the Python path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

from models import StoreTimezone
from scripts.scripts_db import get_scripts_db

FILENAME = 'bq-results-20230125-202210-1674678181880.csv'

csv_file_path = parent_dir / 'data' / FILENAME

BATCH_SIZE = 10000

chunks = pd.read_csv(csv_file_path, chunksize=BATCH_SIZE)

with get_scripts_db() as session:
    for chunk in chunks:
        chunk['timezone_str'].fillna('America/Chicago', inplace=True)
        store_timezones = []
        for index, row in chunk.iterrows():
            store_timezone = StoreTimezone(
                store_id=row['store_id'],
                timezone_str=row['timezone_str']
            )
            store_timezones.append(store_timezone)

        session.add_all(store_timezones)
        session.commit()

print("Data migrated to store_timezones table successfully.")
