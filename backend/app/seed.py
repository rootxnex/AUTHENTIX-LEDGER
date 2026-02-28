"""Seed the database with a default admin user on first startup."""
import sys
import os

# ensure app is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal, engine, Base
from app.models import User, UserRole
from app.auth.jwt import hash_password
from app.config import settings
import structlog

logger = structlog.get_logger(__name__)


def seed():
    # Create all tables if they don't exist
    Base.metadata.create_all(bind=engine)
    logger.info("seed.tables_created")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if existing:
            logger.info("seed.admin_exists", username=settings.ADMIN_USERNAME)
            return

        admin = User(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            unit="National Cyber Coordination Centre",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        logger.info("seed.admin_created", username=settings.ADMIN_USERNAME)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
