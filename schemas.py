from pydantic import BaseModel
from typing import List
from datetime import datetime


class LoginCredentials(BaseModel):
    username: str
    password: str


class RegistrationCredentials(BaseModel):
    username: str
    password: str


class OrganizationCreateSchema(BaseModel):
    name: str


class OrganizationSchema(BaseModel):
    org_id: str
    org_name: str


class MemberSchema(BaseModel):
    user_id: str
    username: str


class TeamSchema(BaseModel):
    team_id: str
    team_name: str
    members: List[MemberSchema]


class TeamDetailsSchema(TeamSchema):
    org_id: str
    creator_id: str
    creator_name: str
    create_datetime: datetime


class TeamCreateSchema(BaseModel):
    team_name: str


class OrganizationDetailsSchema(OrganizationSchema):
    creator_id: str
    creator_name: str
    create_datetime: datetime
    teams: List[TeamSchema]


class OrganizationsSchema(List[OrganizationSchema]):
    pass


class EventSchema(BaseModel):
    id: str
    title: str
    memo: str
    start_point: datetime
    end_point: datetime
    event_priority: str


class MemberEventsSchema(BaseModel):
    user_id: str
    username: str
    events: List[EventSchema]


class TeamEventsMembersSchema(BaseModel):
    team_id: str
    team_name: str
    creator_id: str
    events: List[EventSchema]
    members: List[MemberEventsSchema]


class PostMemberEventsSchema(BaseModel):
    user_id: str
    events: List[EventSchema]


class PostTeamEventsSchema(BaseModel):
    team_id: str
    events: List[EventSchema]


class OrgCalendarSchema(BaseModel):
    teams: List[TeamEventsMembersSchema]


# class EventPrioritySchema(BaseModel):
#     id: str
#     name: str
#     detail: str
#     color: str
#
#
# class EventPrioritySchemaList(List[EventPrioritySchema]):
#     pass


