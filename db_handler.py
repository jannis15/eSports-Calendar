from typing import List, Type

from fastapi import HTTPException
import sqlalchemy.exc
from sqlalchemy.orm import Session as DBSession, joinedload
from sqlalchemy import desc
from sqlalchemy.sql.expression import null

from db_session import SessionLocal
from schemas import RegistrationCredentials, OrganizationSchema, OrganizationsSchema, OrganizationDetailsSchema, \
    MemberSchema, TeamSchema, TeamDetailsSchema, MemberEventsSchema, TeamEventsMembersSchema, EventSchema, \
    OrgCalendarSchema, TeamDetailsMemberSchema, ChangeTeamRoleSchema
from db_models import User, Session, Org, UserOrg, Team, UserTeam, Event, UserEvent, TeamEvent, EventPriority, \
    TeamInvite
import uuid
from datetime import datetime, timezone, timedelta
from utils import add_amount_of_days
from enum import Enum


class EventAllocation(Enum):
    User = 1
    Team = 2


def get_db() -> DBSession:
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


class DBHandler:
    __event_ids_for_optimization = []

    def __get_unique_uuid(self, db: DBSession, table) -> str:
        def generate_uuid() -> str:
            random_uuid = uuid.uuid4()
            return str(random_uuid).replace("-", "")

        def uuid_not_in_db(uuid_str: str, db: DBSession, query_table) -> bool:
            return not db.query(query_table).filter_by(id=uuid_str).first()

        while True:
            tmp_uuid = generate_uuid()

            if uuid_not_in_db(tmp_uuid, db, table):
                return tmp_uuid

    def __get_team_ids_by_org(self, org_id: str, db: Session) -> List[str]:
        org = db.query(Org).filter(Org.id == org_id).first()
        if not org:
            raise HTTPException(status_code=404, detail='Organization not found.')

        team_ids = [team.id for team in org.teams]
        return team_ids

    def __is_owner(self, user_id: str, owner_id: str) -> bool:
        return user_id == owner_id

    def is_user_member_of_org(self, db: DBSession, user_id: str, org_id: str) -> bool:
        user_org = db.query(UserOrg).filter_by(user_id=user_id, org_id=org_id).first()
        return user_org is not None

    def is_user_member_of_team(self, db: DBSession, user_id: str, team_id: str) -> bool:
        user_team = db.query(UserTeam).filter_by(user_id=user_id, team_id=team_id).first()
        return user_team is not None

    def org_exists(self, db: DBSession, org_id: str) -> bool:
        org = db.query(Org).filter_by(id=org_id).first()
        return org is not None

    def user_exists(self, db: DBSession, user_id: str) -> bool:
        user = db.query(User).filter_by(id=user_id).first()
        return user is not None

    def team_exists_in_org(self, db: DBSession, team_id, org_id: str) -> bool:
        team = db.query(Team).filter_by(id=team_id, org_id=org_id).first()
        return team is not None

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
            registration_date=datetime.now(timezone.utc)
        )
        db.add(new_user)
        try:
            db.commit()
            return new_user.id
        except sqlalchemy.exc.IntegrityError:
            raise HTTPException(status_code=401, detail='User already exists in survey.')

    def create_organization(self, user_id, organization_name: str, db: DBSession) -> str:
        current_time = datetime.now(timezone.utc)

        new_org = Org(
            id=self.__get_unique_uuid(db, Org),
            name=organization_name,
            owner_id=user_id,
            owner_datetime=current_time,
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

        if not self.__is_owner(user_id, org.owner_id):
            raise HTTPException(status_code=403, detail='Only the organization owner can delete the organization.')

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

        if not self.__is_owner(session_user_id, org.owner_id) and session_user_id != user_id:
            raise HTTPException(status_code=403, detail='Only the organization owner or the user themselves can '
                                                        'delete the user.')

        if self.__is_owner(user_id, org.owner_id):
            raise HTTPException(status_code=403, detail='The organization owner cannot be deleted.')

        try:
            user_org = db.query(UserOrg).filter_by(user_id=user_id, org_id=org_id).first()
            if user_org is not None:
                db.delete(user_org)
                db.commit()

            return True
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail='Failed to delete user from organization.')

    def create_team(self, user_id, team_name, org_id: str, db: DBSession) -> str:
        if self.is_user_member_of_org(db, user_id, org_id):
            current_time = datetime.now(timezone.utc)
            new_team = Team(
                id=self.__get_unique_uuid(db, Team),
                org_id=org_id,
                name=team_name,
                owner_id=user_id,
                owner_datetime=current_time,
            )
            db.add(new_team)

            try:
                db.commit()

                new_user_team = UserTeam(user_id=user_id, team_id=new_team.id, is_admin=True)
                db.add(new_user_team)
                db.commit()

                return new_team.id
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

        if not self.__is_owner(user_id, team.owner_id):
            raise HTTPException(status_code=403, detail='Only the team owner can delete the team.')

        try:
            db.delete(team)
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail='Failed to delete team.')

    def add_user_to_team(self, session_user_id, team_id, org_id, user_id: str, db: DBSession) -> bool:
        team = db.query(Team).filter_by(id=team_id, org_id=org_id).first()
        if team is None:
            raise HTTPException(status_code=404, detail='Team not found.')

        if not self.__is_owner(session_user_id, team.owner_id) and session_user_id != user_id:
            raise HTTPException(status_code=403, detail='Only the team owner can add others to the team.')

        if self.is_user_member_of_team(db, user_id, team_id):
            raise HTTPException(status_code=409, detail='User already exists in team.')

        try:
            new_user_team = UserTeam(user_id=user_id, team_id=team_id, is_admin=False)
            db.add(new_user_team)
            db.commit()

            return True
        except sqlalchemy.exc.IntegrityError:
            db.rollback()
            raise HTTPException(status_code=500, detail='Error adding user to team.')

    def delete_user_from_team(self, session_user_id, team_id, org_id, user_id: str, db: DBSession) -> bool:
        team = db.query(Team).filter_by(id=team_id, org_id=org_id).first()
        if team is None:
            raise HTTPException(status_code=404, detail='Team not found.')

        if not self.__is_owner(session_user_id, team.owner_id) and session_user_id != user_id:
            raise HTTPException(status_code=403, detail='Only the team owner can delete others from the team')

        if self.__is_owner(user_id, team.owner_id):
            raise HTTPException(status_code=403, detail='The team owner cannot be deleted from the team.')

        user_team = db.query(UserTeam).filter_by(user_id=user_id, team_id=team_id).first()
        if not user_team:
            raise HTTPException(status_code=404, detail='User does not exist in team.')

        try:
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

    def get_org_name_by_id(self, db: DBSession, org_id: str) -> str:
        db_org = db.query(Org).filter(Org.id == org_id).first()
        if db_org:
            return db_org.name
        return ""

    def update_events_for_team(self, session_user_id, org_id, team_id: str, events: List[EventSchema], db: DBSession) \
            -> bool:
        try:
            session_user_team = db.query(UserTeam).filter_by(user_id=session_user_id, team_id=team_id).first()
            team = db.query(Team).filter_by(id=team_id, org_id=org_id).first()
            if team is None:
                raise HTTPException(status_code=404, detail='Team not found.')
            if not (self.__is_owner(session_user_id, team.owner_id) or (session_user_team is not None and
                                                                        session_user_team.is_admin)):
                raise HTTPException(status_code=403, detail='Only the team owner and the admins'
                                                            ' are allowed to modify events here.')

            db_team_events = db.query(TeamEvent).filter(TeamEvent.team_id == team_id).all()

            # Find events to delete
            team_events_to_delete = []
            for db_team_event in db_team_events:
                if db_team_event.event_id not in [event.id for event in events]:
                    team_events_to_delete.append(db_team_event)

            # Delete events from the database
            for team_event in team_events_to_delete:
                self.__event_ids_for_optimization.append(team_event.event_id)
                db.delete(team_event)

            self.__update_events(events, EventAllocation.Team, team_id, db)

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            raise e

    def update_events_for_user(self, user_id: str, events: List[EventSchema], db: DBSession) -> bool:
        try:
            db_user_events = db.query(UserEvent).filter(UserEvent.user_id == user_id).all()

            # Find events to delete
            user_events_to_delete = []
            for db_user_event in db_user_events:
                if db_user_event.event_id not in [event.id for event in events]:
                    user_events_to_delete.append(db_user_event)

            # Delete events from the database
            for user_event in user_events_to_delete:
                self.__event_ids_for_optimization.append(user_event.event_id)
                db.delete(user_event)

            self.__update_events(events, EventAllocation.User, user_id, db)

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            raise e

    def delete_unused_events(self, db: DBSession) -> bool:
        if len(self.__event_ids_for_optimization) != 0:
            unused_events = db.query(Event) \
                .options(joinedload(Event.users), joinedload(Event.teams)) \
                .filter(
                Event.id.in_(self.__event_ids_for_optimization),
                Event.users == null(),
                Event.teams == null()
            ) \
                .all()
            for event in unused_events:
                db.delete(event)
            db.commit()
            self.__event_ids_for_optimization.clear()
        return True

    def __update_events(self, events: List[EventSchema], event_allocation: EventAllocation, allocation_id: str,
                        db: DBSession) -> bool:
        for event in events:
            db_event = None
            if event.id != '':
                db_event = db.query(Event).filter(Event.id == event.id).first()

            event_priority = db.query(EventPriority).filter(EventPriority.name == event.event_priority).first()

            if not event_priority:
                raise HTTPException(status_code=404, detail=f"Event priority '{event.event_priority}' not found.")

            if db_event:
                db_event.title = event.title
                db_event.memo = event.memo
                db_event.start_point = event.start_point
                db_event.end_point = event.end_point
                db_event.priority_id = event_priority.id
            else:
                new_event = Event(
                    id=self.__get_unique_uuid(db, Event),
                    title=event.title,
                    memo=event.memo,
                    start_point=event.start_point,
                    end_point=event.end_point,
                    priority_id=event_priority.id
                )
                db.add(new_event)
                event.id = new_event.id

            if event_allocation == EventAllocation.User:
                user_event = db.query(UserEvent).filter(UserEvent.user_id == allocation_id,
                                                        UserEvent.event_id == event.id).first()
                if not user_event:
                    user_event = UserEvent(user_id=allocation_id, event_id=event.id)
                    db.add(user_event)
            elif event_allocation == EventAllocation.Team:
                team_event = db.query(TeamEvent).filter(TeamEvent.team_id == allocation_id,
                                                        TeamEvent.event_id == event.id).first()
                if not team_event:
                    team_event = TeamEvent(team_id=allocation_id, event_id=event.id)
                    db.add(team_event)

        return True

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

    def __format_events_to_event_schemas(self, events: List[Event]) -> List[EventSchema]:
        events_schemas = []
        for event in events:
            event_schema = EventSchema(
                id=event.id,
                title=event.title,
                memo=event.memo,
                start_point=event.start_point,
                end_point=event.end_point,
                event_priority=event.priority.name,
            )
            events_schemas.append(event_schema)
        return events_schemas

    def __format_user_events_to_event_schemas(self, user_events: List[UserEvent]) -> List[EventSchema]:
        events = []
        for user_event in user_events:
            events.append(user_event.event)
        return self.__format_events_to_event_schemas(events)

    def __format_team_events_to_event_schemas(self, team_events: List[TeamEvent]) -> List[EventSchema]:
        events = []
        for user_event in team_events:
            events.append(user_event.event)
        return self.__format_events_to_event_schemas(events)

    def __format_members_to_member_with_events_schemas(self, session_user_id: str, users: List[UserTeam]) -> List[
        MemberEventsSchema]:
        members = []
        for user_team in users:
            member = MemberEventsSchema(
                user_id=user_team.user_id,
                username=user_team.user.username,
                is_editable=user_team.user_id == session_user_id,
                events=self.__format_user_events_to_event_schemas(user_team.user.events),
            )
            members.append(member)
        return members

    def get_team_with_events_schema(self, session_user_id, team_id: str, db: DBSession) -> TeamEventsMembersSchema:
        db_team = db.query(Team).filter(Team.id == team_id).first()
        session_user_team = db.query(UserTeam).filter_by(user_id=session_user_id, team_id=team_id).first()

        if db_team:
            return TeamEventsMembersSchema(
                team_id=team_id,
                team_name=db_team.name,
                # owner_id=db_team.owner_id,
                is_editable=(db_team.owner_id == session_user_id or
                             (session_user_team is not None and session_user_team.is_admin)),
                events=self.__format_team_events_to_event_schemas(db_team.events),
                members=self.__format_members_to_member_with_events_schemas(session_user_id, db_team.users),
            )

    def get_org_calendar_details(self, session_user_id, org_id: str, db: DBSession) -> OrgCalendarSchema:
        team_ids = self.__get_team_ids_by_org(org_id, db)
        teams = [
            self.get_team_with_events_schema(session_user_id, team_id, db)
            for team_id in team_ids
        ]
        teams.sort(key=lambda team: team.team_name)
        return OrgCalendarSchema(teams=teams)

    def get_organization_details(self, org_id: str, db: DBSession) -> OrganizationDetailsSchema:
        if not self.org_exists(db, org_id):
            raise HTTPException(status_code=404, detail='Organization not found.')

        db_org = db.query(Org).filter(Org.id == org_id).first()

        teams = [
            TeamSchema(team_id=team.id,
                       team_name=team.name,
                       members=[MemberSchema(user_id=user.user_id, username=user.user.username, is_admin=user.is_admin)
                                for user in team.users])
            for team in db_org.teams
        ]
        teams.sort(key=lambda team: team.team_name)
        for team in teams:
            team.members.sort(key=lambda member: member.username)

        teamless_members = (
            db.query(User)
            .join(UserOrg, User.id == UserOrg.user_id)
            .outerjoin(UserTeam, User.id == UserTeam.user_id)
            .filter(UserTeam.user_id.is_(None))
            .filter(UserOrg.org_id == org_id)
            .all()
        )

        teamless_members_schema = [MemberSchema(user_id=user.id, username=user.username, is_admin=False) for user in
                                   teamless_members]
        teamless_members_schema.sort(key=lambda member: member.username)

        teamless_team = TeamSchema(
            team_id="-1",
            team_name="ohne Team",
            members=teamless_members_schema
        )
        teams.insert(0, teamless_team)

        return OrganizationDetailsSchema(
            org_id=db_org.id,
            org_name=db_org.name,
            owner_id=db_org.owner_id,
            owner_name=self.get_username_by_id(db_org.owner_id, db),
            owner_datetime=db_org.owner_datetime,
            teams=teams,
        )

    def get_team_details(self, db: DBSession, org_id, team_id: str) -> TeamDetailsSchema:
        if not self.team_exists_in_org(db, team_id, org_id):
            raise HTTPException(status_code=404, detail='Team not found in organization.')

        db_team = db.query(Team).filter_by(id=team_id).first()

        db_members = db.query(UserTeam).filter_by(team_id=team_id).join(User).order_by(User.username).all()

        members = [
            MemberSchema(user_id=member.user.id, username=member.user.username, is_admin=member.is_admin)
            for member in db_members
        ]

        return TeamDetailsSchema(
            team_id=db_team.id,
            team_name=db_team.name,
            owner_id=db_team.owner_id,
            owner_name=self.get_username_by_id(db_team.owner_id, db),
            owner_datetime=db_team.owner_datetime,
            members=members  # Don't forget to include the sorted members in the return value
        )

    def get_team_members(self, db: DBSession, org_id, team_id: str) -> TeamDetailsMemberSchema:
        if not self.team_exists_in_org(db, team_id, org_id):
            raise HTTPException(status_code=404, detail='Team not found in organization.')

        db_team = db.query(Team).filter_by(id=team_id).first()

        members = [
            MemberSchema(user_id=user.user_id, username=user.user.username, is_admin=user.is_admin)
            for user in db_team.users
        ]

        return TeamDetailsMemberSchema(
            owner_id=db_team.owner_id,
            members=members,
        )

    def get_user_organizations(self, db: DBSession, user_id: str) -> OrganizationsSchema:
        db_user_orgs = db.query(UserOrg).filter_by(user_id=user_id).all()

        organizations = []
        for db_user_org in db_user_orgs:
            db_org = db.query(Org).filter_by(id=db_user_org.org_id).first()
            if db_org:
                organization = OrganizationSchema(
                    org_id=db_org.id,
                    org_name=db_org.name,
                )
                organizations.append(organization)

        return OrganizationsSchema(organizations)

    def change_team_role(self, db: DBSession, org_id, team_id, session_user_id: str, schema: ChangeTeamRoleSchema) \
            -> bool:
        if session_user_id == schema.user_id:
            raise HTTPException(status_code=409, detail='You are not allowed to change your own role.')

        if not self.team_exists_in_org(db, team_id, org_id):
            raise HTTPException(status_code=404, detail='Team not found in organization.')

        if not self.is_user_member_of_team(db, schema.user_id, team_id):
            raise HTTPException(status_code=404, detail='User does not exist in the team.')

        if not self.is_user_member_of_team(db, session_user_id, team_id):
            raise HTTPException(status_code=403, detail='You are not allowed to modify roles.')

        db_team = db.query(Team).filter_by(id=team_id).first()

        if db_team.owner_id == schema.user_id:
            raise HTTPException(status_code=409, detail='The role of the owner cannot be changed as of now.')

        session_user_team = next((user_team for user_team in db_team.users if user_team.user_id == session_user_id),
                                 None)

        if not (db_team.owner_id == session_user_id or session_user_team.is_admin):
            raise HTTPException(status_code=403, detail='You are not allowed to modify roles.')

        user_team = next((user_team for user_team in db_team.users if user_team.user_id == schema.user_id), None)

        if user_team.is_admin == schema.new_admin_state:
            raise HTTPException(status_code=409, detail='The user already has this role.')

        user_team.is_admin = schema.new_admin_state
        db.commit()

        return True

    def validate_invite(self, db_invite: Type[TeamInvite]) -> bool:
        now = datetime.utcnow()
        valid_duration = timedelta(hours=24)
        is_valid = db_invite.create_date_time + valid_duration >= now and not db_invite.used

        return is_valid

    def use_invite(self, db: Session, invite_id, session_user_id: str) -> tuple:
        db_invite = db.query(TeamInvite).filter_by(id=invite_id).first()

        if db_invite:
            is_valid_invite = self.validate_invite(db_invite)
            if is_valid_invite:
                is_member_of_org = self.is_user_member_of_org(db, session_user_id, db_invite.team.org.id)
                if not is_member_of_org:
                    raise HTTPException(status_code=403, detail='You are not a member of the org. You first have to '
                                                                'request access to the organization itself.')

                if self.is_user_member_of_team(db, session_user_id, db_invite.team.id):
                    raise HTTPException(status_code=409, detail='You are already a member of the team. The invite '
                                                                'is still valid for others.')

                new_user_team = UserTeam(user_id=session_user_id, team_id=db_invite.team_id, is_admin=False)
                db.add(new_user_team)
                db_invite.used = True
                db.commit()
            else:
                raise HTTPException(status_code=410, detail='Invite is no longer valid.')
        else:
            raise HTTPException(status_code=404, detail='Invite does not exist.')

        return db_invite.team.org.id, db_invite.team.id

    def generate_invite(self, db: DBSession, org_id, team_id, session_user_id: str) -> str:
        if not self.team_exists_in_org(db, team_id, org_id):
            raise HTTPException(status_code=404, detail='Team not found in organization.')

        if not self.is_user_member_of_team(db, session_user_id, team_id):
            raise HTTPException(status_code=403, detail='You are not allowed to generate invites for this team.')

        db_team = db.query(Team).filter_by(id=team_id).first()
        session_user_team = next((user_team for user_team in db_team.users if user_team.user_id == session_user_id),
                                 None)

        if not (db_team.owner_id == session_user_id or session_user_team.is_admin):
            raise HTTPException(status_code=403, detail='You are not allowed to generate invites for this team.')

        new_team_invite = TeamInvite(id=self.__get_unique_uuid(db, TeamInvite),
                                     create_date_time=datetime.now(timezone.utc),
                                     team_id=team_id)

        db.add(new_team_invite)
        db.commit()
        return new_team_invite.id
