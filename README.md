# Bug Tracker / Issue Tracker

A full-stack Jira-like issue tracker built with FastAPI, PostgreSQL, SQLAlchemy, JWT, React, Tailwind CSS and dnd-kit.

## Features
- User registration and login with JWT bearer tokens
- Argon2 password hashing
- Admin / Developer / Viewer project roles
- Project creation and membership management
- Bug, Task and Feature issues
- Assignment, priority, status and due dates
- Issue comments
- Attachment upload/download
- Search and filtering
- Kanban board with drag-and-drop status updates
- Swagger API docs and pytest tests

## Requirements
- Python 3.10+
- Node.js 20+
- PostgreSQL 14+ (tested design is compatible with PostgreSQL 18)
- Git (optional)

## 1. Database
Create a database named `bug_tracker` in PostgreSQL, or start PostgreSQL using Docker:

```bash
docker compose up -d db
```

## 2. Backend setup (Windows PowerShell)
From the project root:

```powershell
cd backend
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env` and set your PostgreSQL username/password. Then run:

```powershell
alembic upgrade head
python -m uvicorn app.main:app --reload --port 8002
```

Swagger: http://127.0.0.1:8002/docs

If you want to run quickly without PostgreSQL, set `DATABASE_URL=sqlite:///./bug_tracker.db` in `.env`. PostgreSQL is recommended for the assignment.

## 3. Frontend setup
Open a second terminal:

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

Frontend: http://localhost:5173

## First user / admin
Register the first user from the UI or `POST /api/auth/register`.
For a development/demo environment, the first registered user is automatically assigned the global `admin` role. Later users are regular users and must be added to a project with a project role.

## Useful API routes
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/projects`
- `GET /api/projects`
- `POST /api/projects/{project_id}/members`
- `POST /api/issues`
- `GET /api/issues`
- `PATCH /api/issues/{issue_id}`
- `DELETE /api/issues/{issue_id}`
- `GET /api/issues/{issue_id}/comments`
- `POST /api/issues/{issue_id}/comments`
- `POST /api/issues/{issue_id}/attachments`
- `GET /api/issues/{issue_id}/attachments/{filename}`

## Testing
From `backend` with the virtual environment active:

```powershell
pytest -q
```

The tests use an isolated SQLite database and do not modify your PostgreSQL data.

## Notes
- This is a complete starter implementation intended for learning and extension. Configure a strong `SECRET_KEY`, HTTPS, production CORS origins, file size limits, backups and managed secrets before production deployment.
- Uploaded files are stored under `backend/uploads`.
