from sqlalchemy import Column, ForeignKey, String, DateTime, Boolean
from sqlalchemy.orm import relationship

from db_session import Base


class User(Base):
    __tablename__ = "User"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    registration_date = Column(DateTime, nullable=False)
    events = relationship("UserEvent", back_populates="user")
    orgs = relationship("UserOrg", back_populates="user")
    teams = relationship("UserTeam", back_populates="user")


class Session(Base):
    __tablename__ = "Session"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("User.id"), nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    latest_activity = Column(DateTime, nullable=False)


class Event(Base):
    __tablename__ = "Event"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    memo = Column(String, nullable=False)
    start_point = Column(DateTime, nullable=False)
    end_point = Column(DateTime, nullable=False)
    priority_id = Column(String, ForeignKey("EventPriority.id"), nullable=False)
    users = relationship("UserEvent", back_populates="event")
    teams = relationship("TeamEvent", back_populates="event", cascade="all, delete-orphan")
    priority = relationship("EventPriority", back_populates="events")


class EventPriority(Base):
    __tablename__ = "EventPriority"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    detail = Column(String, nullable=False)
    color = Column(String, nullable=False)
    events = relationship("Event", back_populates="priority")


class UserEvent(Base):
    __tablename__ = "UserEvent"

    user_id = Column(String, ForeignKey("User.id"), primary_key=True)
    event_id = Column(String, ForeignKey("Event.id"), primary_key=True)
    user = relationship("User", back_populates="events")
    event = relationship("Event", back_populates="users")


class Org(Base):
    __tablename__ = "Org"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(String, ForeignKey("User.id"))
    owner_datetime = Column(DateTime)
    users = relationship("UserOrg", back_populates="org")
    teams = relationship("Team", back_populates="org")
    codes = relationship("OrgCode", back_populates="org")


class Team(Base):
    __tablename__ = "Team"

    id = Column(String, primary_key=True, index=True)
    org_id = Column(String, ForeignKey("Org.id"), nullable=False)
    name = Column(String, nullable=False)
    owner_id = Column(String, ForeignKey("User.id"))
    owner_datetime = Column(DateTime, nullable=False)
    users = relationship("UserTeam", back_populates="team", passive_deletes=True)
    org = relationship("Org", back_populates="teams")
    events = relationship("TeamEvent", back_populates="team", passive_deletes=True)
    invites = relationship("TeamInvite", back_populates="team", passive_deletes=True)



class UserTeam(Base):
    __tablename__ = "UserTeam"

    user_id = Column(String, ForeignKey("User.id"), primary_key=True)
    team_id = Column(String, ForeignKey("Team.id", ondelete="CASCADE"), primary_key=True)
    is_admin = Column(Boolean, nullable=False, default=False)
    user = relationship("User", back_populates="teams")
    team = relationship("Team", back_populates="users")



class UserOrg(Base):
    __tablename__ = "UserOrg"

    user_id = Column(String, ForeignKey("User.id"), primary_key=True)
    org_id = Column(String, ForeignKey("Org.id"), primary_key=True)
    entry_date_time = Column(DateTime, nullable=False)
    user = relationship("User", back_populates="orgs")
    org = relationship("Org", back_populates="users")


class TeamEvent(Base):
    __tablename__ = "TeamEvent"

    team_id = Column(String, ForeignKey("Team.id", ondelete="CASCADE"), primary_key=True)
    event_id = Column(String, ForeignKey("Event.id"), primary_key=True)
    team = relationship("Team", back_populates="events")
    event = relationship("Event", back_populates="teams", cascade="all, delete-orphan", single_parent=True)


class TeamInvite(Base):
    __tablename__ = "TeamInvite"

    id = Column(String, primary_key=True, index=True)
    create_date_time = Column(DateTime, nullable=False)
    team_id = Column(String, ForeignKey("Team.id", ondelete="CASCADE"), nullable=False)
    used = Column(Boolean, nullable=False, default=False)
    team = relationship("Team", back_populates="invites")


class OrgCode(Base):
    __tablename__ = "OrgCode"

    id = Column(String, primary_key=True, index=True)
    create_date_time = Column(DateTime, nullable=False)
    org_id = Column(String, ForeignKey("Org.id"), nullable=False)
    valid = Column(Boolean, nullable=False, default=True)
    org = relationship("Org", back_populates="codes")
