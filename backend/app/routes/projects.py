from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.dependencies import get_current_user, require_project_access, get_project_role
from app.models import User, Project, ProjectMember, ProjectRole, GlobalRole
from app.schemas.schemas import ProjectCreate, ProjectOut, MemberCreate, MemberOut

router = APIRouter(prefix="/api/projects", tags=["Projects"])

@router.post("", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    key = payload.key.upper()
    if db.query(Project).filter(Project.key == key).first():
        raise HTTPException(status_code=409, detail="Project key already exists")
    project = Project(name=payload.name, key=key, description=payload.description, owner_id=user.id)
    db.add(project)
    db.flush()
    db.add(ProjectMember(project_id=project.id, user_id=user.id, role=ProjectRole.admin))
    db.commit()
    db.refresh(project)
    return project

@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.global_role == GlobalRole.admin:
        return db.query(Project).order_by(Project.created_at.desc()).all()
    return db.query(Project).join(ProjectMember).filter(ProjectMember.user_id == user.id).order_by(Project.created_at.desc()).all()

@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return require_project_access(db, project_id, user)

@router.get("/{project_id}/members", response_model=list[MemberOut])
def list_members(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_project_access(db, project_id, user)
    return db.query(ProjectMember).options(joinedload(ProjectMember.user)).filter_by(project_id=project_id).all()

@router.post("/{project_id}/members", response_model=MemberOut, status_code=201)
def add_member(project_id: int, payload: MemberCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_project_access(db, project_id, user, write=True)
    if get_project_role(db, project_id, user) != ProjectRole.admin:
        raise HTTPException(status_code=403, detail="Only project admins can manage members")
    target = db.query(User).filter(User.email == payload.email.lower()).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    existing = db.query(ProjectMember).filter_by(project_id=project_id, user_id=target.id).first()
    if existing:
        existing.role = payload.role
        member = existing
    else:
        member = ProjectMember(project_id=project_id, user_id=target.id, role=payload.role)
        db.add(member)
    db.commit()
    db.refresh(member)
    return db.query(ProjectMember).options(joinedload(ProjectMember.user)).filter_by(id=member.id).first()

@router.delete("/{project_id}/members/{user_id}", status_code=204)
def remove_member(project_id: int, user_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_project_access(db, project_id, user, write=True)
    if get_project_role(db, project_id, user) != ProjectRole.admin:
        raise HTTPException(status_code=403, detail="Only project admins can remove members")
    member = db.query(ProjectMember).filter_by(project_id=project_id, user_id=user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Membership not found")
    db.delete(member)
    db.commit()
