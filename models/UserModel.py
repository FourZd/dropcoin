from sqlalchemy import Column, Integer, String, DateTime
from models.BaseModel import EntityMeta
from sqlalchemy.orm import relationship

class User(EntityMeta):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True))

    # Relationship to access all bets made by the user
    bets = relationship("CrashBet", back_populates="user")