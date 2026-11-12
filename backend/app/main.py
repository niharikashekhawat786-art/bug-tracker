from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database import Base, engine
from app import models  # noqa: F401 - registers SQLAlchemy models
from app.routes import auth, projects, issues

app = FastAPI(title=settings.app_name, version="1.0.0",
              description="Team issue tracking API with JWT authentication, projects, issues and collaboration.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(issues.router)

@app.get("/", tags=["Health"])
def root():
    return {"message": "Bug Tracker API is running", "docs": "/docs"}

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

@app.on_event("startup")
def create_tables_for_local_development():
    # Alembic is the recommended schema-management mechanism.
    # create_all keeps a fresh local learning setup easy to start.
    Base.metadata.create_all(bind=engine)
