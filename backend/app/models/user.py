import uuid
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    pass
