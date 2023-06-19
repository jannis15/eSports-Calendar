from sqlalchemy import event
from db_models import EventPriority
from sqlalchemy.orm import Session


@event.listens_for(EventPriority.__table__, 'after_create')
def insert_data(target, connection, **kw):
    session = Session(bind=connection)

    data = [
        EventPriority(id="1", name="standard", detail="Standard", color="#edf0f3"),
        EventPriority(id="2", name="notime", detail="Keine Zeit", color="#cc343e"),
        EventPriority(id="3", name="uncertain", detail="Unsicher", color="#efb700"),
        EventPriority(id="4", name="certain", detail="Sicher", color="#008450"),
    ]
    session.add_all(data)
    session.commit()
