from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import decode_token
from app.models import User, Project, ProjectMember, ProjectRole, GlobalRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    subject = decode_token(token)
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.get(User, int(subject))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

def get_project_role(db: Session, project_id: int, user: User) -> ProjectRole | None:
    if user.global_role == GlobalRole.admin:
        return ProjectRole.admin
    membership = db.query(ProjectMember).filter_by(project_id=project_id, user_id=user.id).first()
    return membership.role if membership else None

def require_project_access(db: Session, project_id: int, user: User, write: bool = False) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    role = get_project_role(db, project_id, user)
    if role is None:
        raise HTTPException(status_code=403, detail="You are not a member of this project")
    if write and role == ProjectRole.viewer:
        raise HTTPException(status_code=403, detail="Viewer role cannot modify project data")
    return project
