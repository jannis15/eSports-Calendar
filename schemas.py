from pydantic import BaseModel
from typing import List


class LoginCredentials(BaseModel):
    username: str
    password: str


class RegistrationCredentials(BaseModel):
    username: str
    password: str


class EventPrioritySchema(BaseModel):
    id: str
    name: str
    detail: str
    color: str

class EventPrioritySchemaList(List[EventPrioritySchema]):
    pass