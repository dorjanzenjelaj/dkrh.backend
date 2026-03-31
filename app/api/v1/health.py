from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.dependencies.db import get_db
from fastapi import Depends

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "service": "dkrh.oshee.al API",
        "database": "connected",
    }