from datetime import date
from typing import Annotated, Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

Status = Literal["NOT_STARTED", "ENROLLED", "IN_PROGRESS", "COMPLETED"]
Password = Annotated[str, StringConstraints(strip_whitespace=False, max_length=256)]


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Login(Input):
    email: EmailStr
    password: Password = Field(min_length=1)


class EmployeeCreate(Input):
    employee_code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    password: Password = Field(min_length=12)
    department: str = Field(default="", max_length=150)
    designation: str = Field(default="", max_length=150)
    team_id: str | None = None


class EmployeePatch(Input):
    employee_code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=150)
    email: EmailStr | None = None
    department: str | None = Field(default=None, max_length=150)
    designation: str | None = Field(default=None, max_length=150)
    team_id: str | None = None
    is_active: bool | None = None


class CourseCreate(Input):
    course_code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    category: str = Field(default="", max_length=100)
    provider: str = Field(default="", max_length=150)
    estimated_duration_minutes: int | None = Field(default=None, ge=0)


class CoursePatch(Input):
    course_code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    category: str | None = Field(default=None, max_length=100)
    provider: str | None = Field(default=None, max_length=150)
    estimated_duration_minutes: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class TrackCreate(Input):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    course_ids: list[str] = Field(min_length=1, max_length=200)


class TrackPatch(Input):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=10000)
    is_active: bool | None = None
    course_ids: list[str] | None = Field(default=None, min_length=1, max_length=200)


class TrackCourses(Input):
    course_ids: list[str] = Field(min_length=1, max_length=200)

    @field_validator("course_ids")
    @classmethod
    def unique_courses(cls, values):
        if len(set(values)) != len(values):
            raise ValueError("Courses must be unique")
        return values


class AssignmentCreate(Input):
    employee_id: str
    course_id: str | None = None
    learning_track_id: str | None = None
    target_date: date | None = None
    employee_can_update: bool = True
    employee_can_complete: bool = True
    certificate_required: bool = False
    is_mandatory: bool = False

    @model_validator(mode="after")
    def exactly_one_target(self):
        if bool(self.course_id) == bool(self.learning_track_id):
            raise ValueError("Choose exactly one course or learning track")
        return self


class AssignmentPatch(Input):
    version: int = Field(ge=1)
    target_date: date | None = None
    employee_can_update: bool | None = None
    employee_can_complete: bool | None = None
    certificate_required: bool | None = None
    is_mandatory: bool | None = None
    cancel: bool = False
    reason: str = Field(min_length=3, max_length=2000)


class ProgressPatch(Input):
    status: Status
    version: int = Field(ge=1)
    completion_date: date | None = None
    reason: str | None = Field(default=None, min_length=3, max_length=2000)


class RevokeCertificate(Input):
    reason: str = Field(min_length=3, max_length=2000)


class TeamCreate(Input):
    name: str = Field(min_length=1, max_length=150)
    manager_user_id: str | None = None
