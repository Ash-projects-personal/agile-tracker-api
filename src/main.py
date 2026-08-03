from fastapi import FastAPI
from src.database import init_db
from src.routers import stories, sprints

app = FastAPI(
    title="Agile Tracker API",
    description="Manage sprints, user stories, and track velocity",
    version="0.4.0"
)

app.include_router(stories.router, prefix="/stories", tags=["stories"])
app.include_router(sprints.router, prefix="/sprints", tags=["sprints"])

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return {
        "message": "Agile Tracker API",
        "docs": "/docs"
    }
