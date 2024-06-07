from contextlib import contextmanager
from db import Session
from sqlalchemy.exc import SQLAlchemyError


@contextmanager
def get_scripts_db():
    db = Session()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise e
    finally:
        db.close()
