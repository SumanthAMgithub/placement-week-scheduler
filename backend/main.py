from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.database import Base, engine
from backend.database import models

from backend.routes.companies import router as company_router
from backend.routes.students import router as student_router
from backend.routes.rooms import router as room_router
from backend.routes.panels import router as panel_router
from backend.routes.schedule import router as schedule_router


# Create database tables
Base.metadata.create_all(bind=engine)


# Create FastAPI application
app = FastAPI(
    title="Placement Week Scheduler",
    description="A conflict-aware placement scheduling and dynamic replanning system.",
    version="1.0.0"
)


# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routers
app.include_router(company_router)
app.include_router(student_router)
app.include_router(room_router)
app.include_router(panel_router)
app.include_router(schedule_router)


# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Placement Week Scheduler API",
        "status": "running"
    }


# Health check endpoint
@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }