from sqlalchemy.orm import Session

from app.config import settings
from app.models import User
from app.security import hash_password


def seed_admin_user(db: Session) -> None:
    existing = db.query(User).first()
    if existing is not None:
        return
    user = User(username=settings.admin_username, hashed_password=hash_password(settings.admin_password))
    db.add(user)
    db.commit()
