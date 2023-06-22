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
    name: str
    creator_id: str
    create_datetime: datetime


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


