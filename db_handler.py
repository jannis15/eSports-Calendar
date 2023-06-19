from fastapi import HTTPException
import sqlalchemy.exc
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
from db_session import SessionLocal
from schemas import RegistrationCredentials, EventPrioritySchema, EventPrioritySchemaList
from db_models import User, Session, EventPriority
import uuid
from datetime import datetime
from utils import add_amount_of_days


def get_db() -> DBSession:
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class DBHandler:
    def __get_unique_uuid(self, db: DBSession, table):
        def generate_uuid() -> str:
            random_uuid = uuid.uuid4()
            return str(random_uuid).replace("-", "")

        def uuid_not_in_db(uuid_str: str, db: DBSession, query_table) -> bool:
            return not db.query(query_table).filter_by(id=uuid_str).first()

        while True:
            tmp_uuid = generate_uuid()

            if uuid_not_in_db(tmp_uuid, db, table):
                return tmp_uuid

    def create_user(self, credentials: RegistrationCredentials, db: DBSession) -> bool:
        new_user = User(
            id=self.__get_unique_uuid(db, User),
            username=credentials.username,
            password=credentials.password,
        )
        db.add(new_user)
        try:
            db.commit()
            return True
        except sqlalchemy.exc.IntegrityError:
            raise HTTPException(status_code=409, detail='User already exists in survey.')

    def get_user_id_and_password(self, db: DBSession, username: str):
        db_user = db.query(User.id, User.password).filter_by(username=username).first()
        if db_user is not None:
            return db_user.id, db_user.password
        else:
            return '', ''

    def update_session(self, db: DBSession, user_id: str) -> str:
        current_time = datetime.utcnow()
        new_expiration_date = add_amount_of_days(current_time, 28)

        db_session = db.query(Session) \
            .filter(Session.user_id == user_id) \
            .filter(Session.expiration_date > current_time) \
            .order_by(desc(Session.expiration_date)) \
            .first()

        if db_session:
            tmp_id = db_session.id
            db_session.expiration_date = new_expiration_date
            db_session.latest_activity = current_time
        else:
            tmp_id = self.__get_unique_uuid(db, Session)
            new_session = Session(
                id=tmp_id,
                user_id=user_id,
                expiration_date=new_expiration_date,
                latest_activity=current_time,
            )
            db.add(new_session)

        db.commit()

        return tmp_id

    def verify_user(self, db: DBSession, token: str) -> str:
        current_time = datetime.utcnow()
        db_session = db.query(Session) \
            .filter(Session.id == token) \
            .filter(Session.expiration_date > current_time) \
            .order_by(desc(Session.expiration_date)) \
            .first()

        if db_session is not None:
            db_session.expiration_date = add_amount_of_days(current_time, 28)
            db_session.latest_activity = current_time
            db.commit()

            return db_session.user_id
        else:
            raise HTTPException(status_code=403, detail='Session has expired or was not found.')

    def end_session(self, db: DBSession, token: str) -> bool:
        db_session = db.query(Session) \
            .filter(Session.id == token) \
            .first()

        if db_session is not None:
            current_time = datetime.utcnow()
            db_session.expiration_date = current_time
            db_session.latest_activity = current_time
            db.commit()
            return True
        else:
            return False
        
    def get_event_priorities(self, db: DBSession) -> EventPrioritySchemaList:
        db_event_priorities = db.query(EventPriority).all()

        event_priorities = []
        for db_event_priority in db_event_priorities:
            event_priority = EventPrioritySchema(
                id=db_event_priority.id,
                name=db_event_priority.name,
                detail=db_event_priority.detail,
                color=db_event_priority.color
            )
            event_priorities.append(event_priority)

        return EventPrioritySchemaList(data=event_priorities)

