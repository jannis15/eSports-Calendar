from fastapi import HTTPException
import sqlalchemy.exc
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
from db_session import SessionLocal
from schemas import RegistrationCredentials
from db_models import User, Session, Org, UserOrg, Team, UserTeam
import uuid
from datetime import datetime, timezone
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

    def __is_creator(self, user_id: str, creator_id: str) -> bool:
        return user_id == creator_id

    def is_user_member_of_org(self, db: DBSession, user_id: str, org_id: str) -> bool:
        user_org = db.query(UserOrg).filter_by(user_id=user_id, org_id=org_id).first()
        return user_org is not None

    def org_exists(self, db: DBSession, org_id: str) -> bool:
        org = db.query(Org).filter_by(id=org_id).first()
        return org is not None

    def user_exists(self, db: DBSession, user_id: str) -> bool:
        user = db.query(User).filter_by(id=user_id).first()
        return user is not None

    def get_username_by_id(self, user_id: str, db: DBSession) -> str:
        user = db.query(User).filter_by(id=user_id).first()
        if user:
            return user.username
        else:
            raise HTTPException(status_code=404, detail='User not found.')

    def create_user(self, credentials: RegistrationCredentials, db: DBSession) -> str:
        new_user = User(
            id=self.__get_unique_uuid(db, User),
            username=credentials.username,
            password=credentials.password,
        )
        db.add(new_user)
        try:
            db.commit()
            return new_user.id
        except sqlalchemy.exc.IntegrityError:
            raise HTTPException(status_code=500, detail='User already exists in survey.')

    def create_organization(self, user_id, organization_name: str, db: DBSession) -> str:
        current_time = datetime.now(timezone.utc)

        new_org = Org(
            id=self.__get_unique_uuid(db, Org),
            name=organization_name,
            creator_id=user_id,
            create_time=current_time,
        )
        db.add(new_org)

        try:
            db.commit()

            new_user_org = UserOrg(user_id=user_id,
                                   org_id=new_org.id,
                                   entry_date_time=current_time)
            db.add(new_user_org)
            db.commit()

            return new_org.id
        except sqlalchemy.exc.IntegrityError:
            db.rollback()
            raise HTTPException(status_code=500, detail='Error creating organization.')

    def delete_organization(self, token: str, org_id: str, db: DBSession) -> bool:
        user_id = self.verify_user_session(db, token)

        org = db.query(Org).filter_by(id=org_id).first()

        if org is None:
            raise HTTPException(status_code=404, detail='Organization not found.')

        if not self.__is_creator(user_id, org.creator_id):
            raise HTTPException(status_code=403, detail='Only the organization creator can delete the organization.')

        try:
            db.delete(org)
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail='Failed to delete organization.')

    def delete_user_from_organization(self, token: str, org_id: str, user_id: str, db: DBSession) -> bool:
        session_user_id = self.verify_user_session(db, token)

        org = db.query(Org).filter_by(id=org_id).first()
        if org is None:
            raise HTTPException(status_code=404, detail='Organization not found.')

        if not self.__is_creator(session_user_id, org.creator_id) and session_user_id != user_id:
            raise HTTPException(status_code=403, detail='Only the organization creator or the user themselves can '
                                                        'delete the user.')

        if self.__is_creator(user_id, org.creator_id):
            raise HTTPException(status_code=403, detail='The organization creator cannot be deleted.')

        try:
            user_org = db.query(UserOrg).filter_by(user_id=user_id, org_id=org_id).first()
            if user_org is not None:
                db.delete(user_org)
                db.commit()

            return True
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail='Failed to delete user from organization.')

    def create_team(self, user_id: str, org_id: str, db: DBSession) -> bool:
        if self.is_user_member_of_org(db, user_id, org_id):
            current_time = datetime.now(timezone.utc)
            new_team = Team(
                id=self.__get_unique_uuid(db, Team),
                org_id=org_id,
                name="New Team",
                creator_id=user_id,
                create_time=current_time,
            )
            db.add(new_team)

            try:
                db.commit()

                new_user_team = UserTeam(user_id=user_id, team_id=new_team.id)
                db.add(new_user_team)
                db.commit()

                return True
            except sqlalchemy.exc.IntegrityError:
                db.rollback()
                raise HTTPException(status_code=500, detail='Error creating team.')
        else:
            raise HTTPException(status_code=403, detail='User is not eligible to create a team.')

    def delete_team(self, token: str, team_id: str, db: DBSession) -> bool:
        user_id = self.verify_user_session(db, token)

        team = db.query(Team).filter_by(id=team_id).first()

        if team is None:
            raise HTTPException(status_code=404, detail='Team not found.')

        if not self.__is_creator(user_id, team.creator_id):
            raise HTTPException(status_code=403, detail='Only the team creator can delete the team.')

        try:
            db.delete(team)
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail='Failed to delete team.')

    def add_user_to_team(self, token: str, team_id: str, org_id: str, user_id: str, db: DBSession) -> bool:
        session_user_id = self.verify_user_session(db, token)

        # Check if the user is a member of the organization
        if not self.is_user_member_of_org(db, user_id, org_id):
            raise HTTPException(status_code=403, detail='User is not a member of the organization.')

        # Check if the session user is a member of the organization and a creator of the team
        if not self.is_user_member_of_org(db, session_user_id, org_id):
            raise HTTPException(status_code=403, detail='You are not a member of the organization.')

        team = db.query(Team).filter_by(id=team_id, org_id=org_id).first()
        if team is None:
            raise HTTPException(status_code=404, detail='Team not found.')

        # Check if the session user is the creator of the team
        if not self.__is_creator(session_user_id, team.creator_id):
            raise HTTPException(status_code=403, detail='Only the team creator can add users to the team.')

        try:
            # Add the user to the team
            new_user_team = UserTeam(user_id=user_id, team_id=team_id)
            db.add(new_user_team)
            db.commit()

            return True
        except sqlalchemy.exc.IntegrityError:
            db.rollback()
            raise HTTPException(status_code=500, detail='Error adding user to team.')

    def delete_user_from_team(self, token: str, team_id: str, user_id: str, db: DBSession) -> bool:
        session_user_id = self.verify_user_session(db, token)

        team = db.query(Team).filter_by(id=team_id).first()
        if team is None:
            raise HTTPException(status_code=404, detail='Team not found.')

        org_id = team.org_id
        if not self.is_user_member_of_org(db, session_user_id, org_id):
            raise HTTPException(status_code=403, detail='User is not a member of the organization.')

        if not self.__is_creator(session_user_id, team.creator_id) and session_user_id != user_id:
            raise HTTPException(status_code=403, detail='Only the team creator or the user themselves can delete the '
                                                        'user from the team.')

        if self.__is_creator(user_id, team.creator_id):
            raise HTTPException(status_code=403, detail='The team creator cannot be deleted from the team.')

        try:
            user_team = db.query(UserTeam).filter_by(user_id=user_id, team_id=team_id).first()
            if user_team is not None:
                db.delete(user_team)
                db.commit()

            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail='Failed to delete user from team.')

    def add_yourself_to_team(self, token: str, team_id: str, org_id: str, db: DBSession) -> bool:
        session_user_id = self.verify_user_session(db, token)
        return self.add_user_to_team(token, team_id, org_id, session_user_id, db)

    def add_user_to_organization(self, db: DBSession, user_id: str, org_id: str) -> None:
        current_time = datetime.utcnow()
        if self.is_user_member_of_org(db, user_id, org_id):
            raise HTTPException(status_code=409, detail='User is already a member of the organization.')

        if not self.user_exists(db, user_id):
            raise HTTPException(status_code=404, detail='User not found.')

        if not self.org_exists(db, org_id):
            raise HTTPException(status_code=404, detail='Organization not found.')

        try:
            new_user_org = UserOrg(
                user_id=user_id,
                org_id=org_id,
                entry_date_time=current_time,
            )
            db.add(new_user_org)
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail='Failed to add user to organization.')

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

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail='Failed to update session.')

        return tmp_id

    def verify_user_session(self, db: DBSession, token: str) -> str:
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
