from sqlalchemy import Column, Integer, String
from models.BaseModel import EntityMeta
from sqlalchemy.orm import relationship

class CrashHash(EntityMeta):
    __tablename__ = 'crash_hashes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    hash = Column(String, nullable=False)

    current_game_states = relationship("CrashState", foreign_keys="CrashState.current_game_hash_id", back_populates="current_game_hash")
    last_game_states = relationship("CrashState", foreign_keys="CrashState.last_game_hash_id", back_populates="last_game_hash")