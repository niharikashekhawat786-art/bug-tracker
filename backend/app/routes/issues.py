from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pathlib import Path
from uuid import uuid4
from app.database import get_db
from app.core.config import settings
from app.dependencies import get_current_user, require_project_access, get_project_role
from app.models import User, Issue, Comment, Attachment, ProjectRole
from app.schemas.schemas import IssueCreate, IssueUpdate, IssueOut, CommentCreate, CommentOut

router = APIRouter(prefix="/api", tags=["Issues and Collaboration"])

@router.post("/issues", response_model=IssueOut, status_code=201)
def create_issue(payload: IssueCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_project_access(db, payload.project_id, user, write=True)
    if payload.assignee_id:
        from app.models import ProjectMember
        if not db.query(ProjectMember).filter_by(project_id=payload.project_id, user_id=payload.assignee_id).first():
            raise HTTPException(status_code=400, detail="Assignee must be a project member")
    issue = Issue(**payload.model_dump(), reporter_id=user.id)
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue

@router.get("/issues", response_model=list[IssueOut])
def list_issues(project_id: int | None = None, status: str | None = None, priority: str | None = None,
                issue_type: str | None = None, assignee_id: int | None = None, q: str | None = Query(default=None, max_length=120),
                db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Issue)
    if project_id is not None:
        require_project_access(db, project_id, user)
        query = query.filter(Issue.project_id == project_id)
    else:
        from app.models import ProjectMember
        if user.global_role.value != "admin":
            project_ids = [m.project_id for m in db.query(ProjectMember).filter_by(user_id=user.id).all()]
            query = query.filter(Issue.project_id.in_(project_ids))
    if status: query = query.filter(Issue.status == status)
    if priority: query = query.filter(Issue.priority == priority)
    if issue_type: query = query.filter(Issue.issue_type == issue_type)
    if assignee_id: query = query.filter(Issue.assignee_id == assignee_id)
    if q: query = query.filter(or_(Issue.title.ilike(f"%{q}%"), Issue.description.ilike(f"%{q}%")))
    return query.order_by(Issue.updated_at.desc()).limit(500).all()

@router.get("/issues/{issue_id}", response_model=IssueOut)
def get_issue(issue_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    issue = db.get(Issue, issue_id)
    if not issue: raise HTTPException(status_code=404, detail="Issue not found")
    require_project_access(db, issue.project_id, user)
    return issue

@router.patch("/issues/{issue_id}", response_model=IssueOut)
def update_issue(issue_id: int, payload: IssueUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    issue = db.get(Issue, issue_id)
    if not issue: raise HTTPException(status_code=404, detail="Issue not found")
    require_project_access(db, issue.project_id, user, write=True)
    changes = payload.model_dump(exclude_unset=True)
    if "assignee_id" in changes and changes["assignee_id"] is not None:
        from app.models import ProjectMember
        if not db.query(ProjectMember).filter_by(project_id=issue.project_id, user_id=changes["assignee_id"]).first():
            raise HTTPException(status_code=400, detail="Assignee must be a project member")
    for key, value in changes.items(): setattr(issue, key, value)
    db.commit()
    db.refresh(issue)
    return issue

@router.delete("/issues/{issue_id}", status_code=204)
def delete_issue(issue_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    issue = db.get(Issue, issue_id)
    if not issue: raise HTTPException(status_code=404, detail="Issue not found")
    require_project_access(db, issue.project_id, user, write=True)
    if get_project_role(db, issue.project_id, user) != ProjectRole.admin and issue.reporter_id != user.id:
        raise HTTPException(status_code=403, detail="Only project admins or the reporter can delete this issue")
    db.delete(issue)
    db.commit()

@router.get("/issues/{issue_id}/comments", response_model=list[CommentOut])
def list_comments(issue_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    issue = db.get(Issue, issue_id)
    if not issue: raise HTTPException(status_code=404, detail="Issue not found")
    require_project_access(db, issue.project_id, user)
    return db.query(Comment).filter_by(issue_id=issue_id).order_by(Comment.created_at.asc()).all()

@router.post("/issues/{issue_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(issue_id: int, payload: CommentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    issue = db.get(Issue, issue_id)
    if not issue: raise HTTPException(status_code=404, detail="Issue not found")
    require_project_access(db, issue.project_id, user, write=True)
    comment = Comment(body=payload.body, issue_id=issue_id, author_id=user.id)
    db.add(comment); db.commit(); db.refresh(comment)
    return comment

@router.post("/issues/{issue_id}/attachments", status_code=201)
async def upload_attachment(issue_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    issue = db.get(Issue, issue_id)
    if not issue: raise HTTPException(status_code=404, detail="Issue not found")
    require_project_access(db, issue.project_id, user, write=True)
    data = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds upload size limit")
    safe_name = Path(file.filename or "upload").name
    stored = f"{uuid4().hex}_{safe_name}"
    folder = Path(settings.upload_dir); folder.mkdir(parents=True, exist_ok=True)
    (folder / stored).write_bytes(data)
    item = Attachment(original_name=safe_name, stored_name=stored, issue_id=issue_id, uploaded_by_id=user.id)
    db.add(item); db.commit(); db.refresh(item)
    return {"id": item.id, "filename": item.original_name, "download_url": f"/api/issues/{issue_id}/attachments/{stored}"}

@router.get("/issues/{issue_id}/attachments")
def list_attachments(issue_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    issue = db.get(Issue, issue_id)
    if not issue: raise HTTPException(status_code=404, detail="Issue not found")
    require_project_access(db, issue.project_id, user)
    rows = db.query(Attachment).filter_by(issue_id=issue_id).all()
    return [{"id": x.id, "filename": x.original_name, "stored_name": x.stored_name} for x in rows]

@router.get("/issues/{issue_id}/attachments/{stored_name}")
def download_attachment(issue_id: int, stored_name: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    issue = db.get(Issue, issue_id)
    if not issue: raise HTTPException(status_code=404, detail="Issue not found")
    require_project_access(db, issue.project_id, user)
    item = db.query(Attachment).filter_by(issue_id=issue_id, stored_name=stored_name).first()
    if not item: raise HTTPException(status_code=404, detail="Attachment not found")
    path = Path(settings.upload_dir) / item.stored_name
    if not path.is_file(): raise HTTPException(status_code=404, detail="File missing from storage")
    return FileResponse(path, filename=item.original_name)
