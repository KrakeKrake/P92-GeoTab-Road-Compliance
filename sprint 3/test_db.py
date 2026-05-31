from database import SessionLocal
from db_models import LicenceClass

db = SessionLocal()

try:
    rows = db.query(LicenceClass).all()

    for row in rows:
        print(row.licence_class_id, row.display_name, row.rank_value)

finally:
    db.close()