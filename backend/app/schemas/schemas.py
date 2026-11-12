from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.entities import ProjectRole, IssueType, IssueStatus, Priority, GlobalRole

class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    global_role: GlobalRole
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    key: str = Field(min_length=2, max_length=12, pattern=r"^[A-Za-z][A-Za-z0-9]+$")
    description: str | None = None

class ProjectOut(BaseModel):
    id: int
    name: str
    key: str
    description: str | None
    owner_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MemberCreate(BaseModel):
    email: EmailStr
    role: ProjectRole = ProjectRole.developer

class MemberOut(BaseModel):
    id: int
    user_id: int
    role: ProjectRole
    user: UserOut
    model_config = ConfigDict(from_attributes=True)

class IssueCreate(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    description: str | None = None
    issue_type: IssueType = IssueType.bug
    status: IssueStatus = IssueStatus.backlog
    priority: Priority = Priority.medium
    project_id: int
    assignee_id: int | None = None
    due_date: datetime | None = None

class IssueUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=240)
    description: str | None = None
    issue_type: IssueType | None = None
    status: IssueStatus | None = None
    priority: Priority | None = None
    assignee_id: int | None = None
    due_date: datetime | None = None

class IssueOut(BaseModel):
    id: int
    title: str
    description: str | None
    issue_type: IssueType
    status: IssueStatus
    priority: Priority
    project_id: int
    reporter_id: int
    assignee_id: int | None
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)

class CommentOut(BaseModel):
    id: int
    body: str
    issue_id: int
    author_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
