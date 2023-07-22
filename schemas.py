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
    is_admin: bool


class TeamSchema(BaseModel):
    team_id: str
    team_name: str
    members: List[MemberSchema]


class TeamDetailsSchema(BaseModel):
    team_id: str
    team_name: str
    owner_id: str
    owner_name: str
    owner_datetime: datetime


class TeamDetailsMemberSchema(BaseModel):
    owner_id: str
    members: List[MemberSchema]


class TeamCreateSchema(BaseModel):
    team_name: str


class OrganizationDetailsSchema(OrganizationSchema):
    owner_id: str
    owner_name: str
    owner_datetime: datetime
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
    is_editable: bool
    events: List[EventSchema]


class PostMemberEventsSchema(BaseModel):
    user_id: str
    events: List[EventSchema]


class PostTeamEventsSchema(BaseModel):
    team_id: str
    events: List[EventSchema]


class PostOrgCalendarSchema(BaseModel):
    memberEvents: PostMemberEventsSchema
    teamsEvents: List[PostTeamEventsSchema]


class TeamEventsMembersSchema(BaseModel):
    team_id: str
    team_name: str
    # owner_id: str
    is_editable: bool
    events: List[EventSchema]
    members: List[MemberEventsSchema]


class OrgCalendarSchema(BaseModel):
    teams: List[TeamEventsMembersSchema]


class ChangeTeamRoleSchema(BaseModel):
    user_id: str
    new_admin_state: bool


# class EventPrioritySchema(BaseModel):
#     id: str
#     name: str
#     detail: str
#     color: str
#
#
# class EventPrioritySchemaList(List[EventPrioritySchema]):
#     pass


