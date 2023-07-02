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
    creator_id: str
    creator_name: str
    creator_datetime: str


class TeamCreateSchema(BaseModel):
    team_name: str


class OrganizationDetailsSchema(OrganizationSchema):
    creator_id: str
    creator_name: str
    create_datetime: datetime
    members: List[MemberSchema]
    teams: List[TeamSchema]


class OrganizationsSchema(List[OrganizationSchema]):
    pass

# class EventPrioritySchema(BaseModel):
#     id: str
#     name: str
#     detail: str
#     color: str
#
#
# class EventPrioritySchemaList(List[EventPrioritySchema]):
#     pass


