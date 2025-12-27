from pydantic import BaseModel
from typing import Optional
from datetime import date


class LoginSchema(BaseModel):
    login: str
    password: str


class RegisterSchema(BaseModel):
    fio: str
    phone: str
    login: str
    password: str



class RequestCreateSchema(BaseModel):
    climate_tech_type: str
    climate_tech_model: str
    problem_description: str


class RequestUpdateSchema(BaseModel):
    status: Optional[str] = None
    problem_description: Optional[str] = None
    master_id: Optional[int] = None
    completion_date: Optional[date] = None


class ExtendDeadlineSchema(BaseModel):
    request_id: int
    new_date: date


class CommentCreateSchema(BaseModel):
    request_id: int
    message: str
