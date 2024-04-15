from sqlalchemy import Column, Integer, String, DateTime
from models.BaseModel import EntityMeta


class User(EntityMeta):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True))